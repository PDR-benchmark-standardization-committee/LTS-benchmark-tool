# coding: utf-8
import os
import glob
import argparse
import re

from logging import getLogger, Formatter, StreamHandler, FileHandler, DEBUG, INFO
import matplotlib.pyplot as plt
import pandas as pd
import dataloader
from indicator_evaluation import CalcIndicator

import indicator_utils
import utils

def main(args):
    # File output handler for save folder
    if args.save_folder:
        log_file_name2 = os.path.join(args.save_folder, '{}.log'.format(__name__))
        file_handler2 = FileHandler(log_file_name2, 'a')
        file_handler2.setLevel(DEBUG)
        file_handler2.setFormatter(formatter)
        logger.addHandler(file_handler2)

    for track in args.track:
        logger.debug('- {}, {} evaluation START -'.format(args.trajection_folder, track))
        
        # Load data config 
        data_config_path = glob.glob(os.path.join(args.ground_truth_folder, '*.ini'))[0]
        conf = dataloader.config(track, args.ground_truth_folder, config_file=data_config_path)

        # Directory path to evaluate
        tra_dname = os.path.join(args.trajection_folder, track)
        logger.debug('tra_dname:{}'.format(tra_dname))

        # Load groundtruth files
        map_size = dataloader.map_size(conf['map_dname'], conf['map_size_fname'])
        map_image = dataloader.map_image(conf['map_dname'], conf['map_image_fname'])    
        area_info = dataloader.area_info(conf['map_dname'], conf['area_fname'])     
        BLE_info = dataloader.BLE_info(conf['BLE_dname'], conf['BLE_info_fname'])     
        map_color = dataloader.map_color(conf['map_obstacle_color'], conf['map_trajectory_color'], conf['map_ref_color'], conf['map_BLE_color'])
        map_makersize = dataloader.map_makersize(conf['map_trajectory_size'], conf['map_ref_size'], conf['map_BLE_size'], conf['map_grid'])

        # Create result save directory
        if args.save_folder:
            result_basedir = os.path.join(args.save_folder, track)
        else:
            result_basedir = os.path.join(tra_dname, 'result')
        indicator_savedir = os.path.join(result_basedir, 'indicator') 
        
        for dir_path in [result_basedir, indicator_savedir]:
            utils.create_dir(dir_path)

        extension_types = ['*.txt', '*.csv']
        tra_files = []
        for ext_type in extension_types:
            keyword = os.path.join(tra_dname, ext_type)
            tra_files.extend([os.path.split(file_path)[-1] for file_path in sorted(glob.glob(keyword, recursive=True))])
            
        if args.file:
            tra_files = args.file

        logger.debug('trajection files:{}'.format(tra_files))

        # Instance to calculate indicator
        evaluation_indicator = CalcIndicator()
        indicator_holder = indicator_utils.IndicatorHolder()
        
        for tra_filename in tra_files:
            logger.debug('{} Evaluation START'.format(tra_filename))
            print('{} evaluation progress...'.format(tra_filename))
 
            # Load trajectory files
            tra_data = dataloader.load_point(tra_dname, tra_filename)
            tra_num = re.sub("\\D", "", tra_filename)

            # Load ground truth files
            ref_point = dataloader.load_point(conf['ref_dname'], conf['ref_fname'].format(tra_num))
            ans_point = dataloader.load_point(conf['ans_dname'], conf['ans_fname'].format(tra_num))
            ALIP_info = dataloader.ALIP_info(conf['ALIP_dname'], conf['ALIP_info_fname'].format(tra_num))

            indicator_holder.add_indicator_percentile('file_name', tra_filename)

            # prepare evaluation point
            if ref_point is None:
                evaluation_point = ans_point
            else:
                evaluation_point = dataloader.drop_ans_duplicated_with_ref(ans_point, ref_point)

            if ALIP_info is None:
                eval_point_ALAP = ans_point
                eval_point_ALIP = pd.DataFrame(index=[], columns=['unixtime', 'x_position_m', 'y_position_m'])
            else:
                eval_point_ALAP = dataloader.filter_evaluation_data_ALIP(evaluation_point, ALIP_info, ALIP_flag=False)
                eval_point_ALIP = dataloader.filter_evaluation_data_ALIP(evaluation_point, ALIP_info, ALIP_flag=True)
                 
            """
            if area_info:
                which_area = indicator_utils.area_of_ans(eval_point_ALIP, area_info)
                which_area_all.extend(which_area)
            """

            # CE
            if 'CE' in args.indicators:
                CE = evaluation_indicator.CE_calculation(tra_data, eval_point_ALAP)
                CE_percentile = indicator_utils.calc_percentile(CE['CE'], args.CE_percentile)
                indicator_holder.add_indicator_percentile(f'CE{args.CE_percentile}', CE_percentile)

                indicator_holder.add_total_indicator(f'CE{args.CE_percentile}', CE['CE'])

                indicator_utils.calc_CE_map(CE, map_size)
                CE_savedir = os.path.join(indicator_savedir, 'CE')
                utils.create_dir(CE_savedir) 

                indicator_utils.save_indicator(data=CE, save_dir=CE_savedir, save_filename=f'Traj_No{tra_num}_CE.csv')
                CE_hist = indicator_utils.draw_histgram(data=CE['CE'], indicator_name='CE', percentile=args.CE_percentile)
                indicator_utils.save_figure(CE_hist, save_dir=CE_savedir, save_filename=f'Traj_No{tra_num}_CE_histgram.png')
            
                CE_map = indicator_utils.draw_CE_map(CE, map_image, map_size, indicator_name='CE')
                indicator_utils.save_figure(CE_map, save_dir=CE_savedir, save_filename=f'Traj_No{tra_num}_CE_map.png')

            # CP
            if 'CP' in args.indicators:
                CP = evaluation_indicator.CP_calculation(tra_data, eval_point_ALAP, band_width=None)
                CP_percentile = indicator_utils.calc_percentile(CP['CP'], args.CP_percentile)
                indicator_holder.add_indicator_percentile(f'CP{args.CP_percentile}', CP_percentile)

                indicator_holder.add_total_indicator(f'CP{args.CP_percentile}', CP['CP'])

                CP_savedir = os.path.join(indicator_savedir, 'CP')
                utils.create_dir(CP_savedir) 

                indicator_utils.save_indicator(data=CP, save_dir=CP_savedir, save_filename=f'Traj_No{tra_num}_CP.csv')
                CP_hist = indicator_utils.draw_histgram(data=CP['CP'], indicator_name='CP', percentile=args.CP_percentile)
                indicator_utils.save_figure(CP_hist, save_dir=CP_savedir, save_filename=f'Traj_No{tra_num}_CP_histgram.png')

            # Area-weighted CA
            if 'CA' in args.indicators: 
                if args.area_weights is None:
                    area_weights = indicator_utils.get_CA_area_weights(evaluation_point, area_info)
                else:
                    area_weights = dataloader.area_weights_config(track, args.area_weights)
                
                if area_weights is None:
                    logger.debug('CA is calculated for whole area')
                    if args.CA_hist:
                        CA, CA_fig = evaluation_indicator.CA_2Dhistgram_calculation(tra_data, evaluation_point)
                    else:
                        CA, CA_fig = evaluation_indicator.CA_KernelDensity_calculation(tra_data, evaluation_point, band_width=None)
                    CA_df = pd.DataFrame({'CA': CA}, index=[0])
                
                else:
                    logger.debug('CA is calculated for each area division')
                    CA, CA_df, CA_fig = evaluation_indicator.Area_weighted_CA_calculation(tra_data, evaluation_point, area_info, area_weights, args.CA_hist)
                
                indicator_holder.add_indicator_percentile('CA', CA)
                CA_savedir = os.path.join(indicator_savedir, 'CA')
                utils.create_dir(CA_savedir) 
                indicator_utils.save_dataframe(CA_savedir, f'Traj_No{tra_num}_CA.csv', CA_df)
                       
                if isinstance(CA_fig, list):
                    for i in range(len(CA_fig)):
                        CA_fig[i].suptitle(f'Traj_No{tra_num}_area{i+1}_CA')
                        indicator_utils.save_figure(CA_fig[i], save_dir=CA_savedir, save_filename=f'Traj_No{tra_num}_area{i+1}_CA.png')        
                else:
                    CA_fig.suptitle(f'Traj_No{tra_num}_CA')
                    indicator_utils.save_figure(CA_fig, save_dir=CA_savedir, save_filename=f'Traj_No{tra_num}_CA.png')
                
            # EAG
            if 'EAG' in args.indicators and not ref_point.empty and not eval_point_ALIP.empty:
                EAG = evaluation_indicator.EAG_calculation(tra_data, ref_point, eval_point_ALIP) 

                EAG_percentile = indicator_utils.calc_percentile(EAG['EAG'], args.EAG_percentile)
                indicator_holder.add_indicator_percentile(f'EAG{args.EAG_percentile}', EAG_percentile)

                indicator_holder.add_total_indicator(f'EAG{args.EAG_percentile}', EAG['EAG'])

                EAG_savedir = os.path.join(indicator_savedir, 'EAG')
                utils.create_dir(EAG_savedir) 
                
                indicator_utils.save_indicator(data=EAG, save_dir=EAG_savedir, save_filename=f'Traj_No{tra_num}_EAG.csv')
                EAG_hist = indicator_utils.draw_histgram(data=EAG['EAG'], indicator_name='EAG', percentile=args.EAG_percentile)
                indicator_utils.save_figure(EAG_hist, save_dir=EAG_savedir, save_filename=f'Traj_No{tra_num}_EAG_histgram.png')

            # Requirement for Moving Velocity 
            if 'requirement_velocity' in args.indicators:
                moving_velocity_df = evaluation_indicator.requirement_moving_velocity_check(tra_data, args.velocity)
                indicator_holder.add_indicator_percentile('requirement_velocity', moving_velocity_df['velocity'].mean())
                velocity_savedir = os.path.join(indicator_savedir, 'requirement_velocity')
                utils.create_dir(velocity_savedir)
                indicator_utils.save_dataframe(velocity_savedir, f'Traj_No{tra_num}_moving_velocity.csv', moving_velocity_df)

            # Requirement for obstacle avoidance
            if 'requirement_obstacle' in args.indicators:
                obstacle_df = evaluation_indicator.requirement_obstacle_check(tra_data, map_image, map_size)
                if len(obstacle_df) == 0:
                    obstacle_ratio = -1
                else:
                    obstacle_ratio = sum(obstacle_df['obstacle_cordinate_count']) / sum(obstacle_df['check_cordinate_count'])
            
                indicator_holder.add_indicator_percentile('requirement_obstacle', obstacle_ratio)
                obstacle_savedir = os.path.join(indicator_savedir, 'requirement_obstacle')
                utils.create_dir(obstacle_savedir)
                indicator_utils.save_dataframe(obstacle_savedir, f'Traj_No{tra_num}_obstacle.csv', obstacle_df)

            if 'requirement_coverage' in args.indicators:
                eval_num = len(evaluation_point)
                corr_num = len(evaluation_indicator.extract_correspond_point(tra_data, evaluation_point))
                coverage = corr_num / eval_num * 100
                indicator_holder.add_indicator_percentile('requirement_coverage', coverage)

            logger.debug('{} Evaluation END'.format(tra_filename))

            # Draw trajectory
            Tra_savedir = os.path.join(indicator_savedir, 'Trajectory')
            utils.create_dir(Tra_savedir)
            Trajectory_image = indicator_utils.draw_trajectory(tra_data, map_image, map_size, f'Trajectory_No{tra_num}', ref_point, BLE_info, map_color, map_makersize)
            indicator_utils.save_figure(Trajectory_image, save_dir=Tra_savedir, save_filename=f'Tra_No{tra_num}.png')

        # Show each file's results
        file_indicator_summary = indicator_holder.summarize_file_indicator()
        utils.stdout_dataframe(file_indicator_summary, title='file indicator')
        utils.save_csv(save_file=file_indicator_summary, save_dir=indicator_savedir, save_filename='file_indicator.csv')

        # Show total results
        total_indicator = indicator_holder.summarize_total_indicator()
        utils.stdout_dataframe(total_indicator, title='total indicator')
        utils.save_csv(save_file=total_indicator, save_dir=indicator_savedir, save_filename='total_indicator.csv')
        
        # Draw histgram and cumulative sum for total CE and EAG
        if 'CE' in args.indicators:
            CE_total = indicator_holder.indicator_total[f'CE{args.CE_percentile}']
            CE_total_hist = indicator_utils.draw_histgram(data=CE_total, indicator_name='CE', percentile=args.CE_percentile)
            indicator_utils.save_figure(CE_total_hist, save_dir=CE_savedir, save_filename='CE_total_histgram.png')
            CE_cumulative_sum = indicator_utils.draw_cumulative_sum(CE_total.values.tolist(), 'CE')
            indicator_utils.save_figure(CE_cumulative_sum, save_dir=CE_savedir, save_filename='CE_total_cumulative_sum.png')

        if 'EAG' in args.indicators:
            EAG_total = indicator_holder.indicator_total[f'EAG{args.EAG_percentile}']
            EAG_total_hist = indicator_utils.draw_histgram(data=EAG_total, indicator_name='EAG', percentile=args.EAG_percentile)
            indicator_utils.save_figure(EAG_total_hist, save_dir=EAG_savedir, save_filename='EAG_total_histgram.png')
            EAG_cumulative_sum = indicator_utils.draw_cumulative_sum(EAG_total.values.tolist(), 'EAG')
            indicator_utils.save_figure(EAG_cumulative_sum, save_dir=EAG_savedir, save_filename='EAG_total_cumulative_sum.png')

        logger.debug('- {}, {} evaluation END -'.format(args.trajection_folder, track))
    
if __name__ == '__main__':  

    parser = argparse.ArgumentParser(description='XDR Challenge Evaluation Setting')

    parser.add_argument('trajection_folder', type=str, help='Set trajection folder name')

    parser.add_argument('ground_truth_folder', type=str, help='Set ground truth folder name')

    parser.add_argument('--save_folder', type=str, help='Set save folder name')
    
    parser.add_argument('--VDR', action='store_const', dest='track', default=['VDR','PDR'],
                        const=['VDR'],help='Set  VDR track')
    
    parser.add_argument('--PDR', action='store_const', dest='track', default=['VDR','PDR'],
                        const=['PDR'],help='Set  PDR track')
    
    parser.add_argument('--file', nargs='*', help='Select file name for evaluation')
                        
    parser.add_argument('--CE', action='append_const', dest='indicators', default=[],
                        const='CE', help='Calculate Circular Error')
    
    parser.add_argument('--CE_percentile', type=int, default=50,
                        help='Calculate percentile of Circular Error')

    parser.add_argument('--CP', action='append_const', dest='indicators', default=[],
                        const='CP', help='Calculate Circular Precision')

    parser.add_argument('--CP_percentile', type=int, default=50,
                        help='Calculate percentile of Circular Presicion')

    parser.add_argument('--CA', action='append_const', dest='indicators', default=[],
                        const='CA', help='Calculate Area-weighted Circular Error Distribution Deviation')
    
    parser.add_argument('--area_weights', default=None, help='area weights configuration path')

    parser.add_argument('--CA_hist', action='store_true', help='Calculate CA by 2D hisgram')

    parser.add_argument('--band_width', type=float, default=None, help='band width for kernel density')

    parser.add_argument('--EAG', action='append_const', dest='indicators', default=[],
                        const='EAG', help='Calculate Error Accumulation Gradient')

    parser.add_argument('--EAG_percentile', type=int, default=50,
                        help='Calculate percentile of Error Accumulation Gradient')

    parser.add_argument('--requirement_velocity', action='append_const', dest='indicators', default=[],
                        const='requirement_velocity', help='Calculate requirement for moving velocity')
    
    parser.add_argument('--velocity', type=float, default=1.5, help='appropriate walking velocity (unit: m/s)')

    parser.add_argument('--requirement_obstacle', action='append_const', dest='indicators', default=[],
                        const='requirement_obstacle', help='Calculate requirement for obstacle avoidance')
    
    parser.add_argument('--requirement_coverage', action='append_const', dest='indicators', default=[],
                        const='requirement_coverage', help='Calculate requirement for coverage')

    parser.add_argument('--debug', action='store_const', dest='level', default=INFO, const=DEBUG, 
                        help='Logger debug mode')

    args = parser.parse_args()
    args.indicators = ['CE', 'CA', 'EAG', 'requirement_velocity', 'requirement_obstacle', 'requirement_coverage'] if not args.indicators else args.indicators
    
    #　Logger setting
    logger = getLogger(__name__)
    logger.setLevel(DEBUG)

    formatter = Formatter('%(asctime)s - %(name)s - %(message)s')

    # Standard output handler
    stream_handler = StreamHandler()
    stream_handler.setLevel(args.level)
    stream_handler.setFormatter(formatter)

    # File output handler
    log_file_name = os.path.basename(__file__) + '.log'
    file_handler = FileHandler(log_file_name, 'a')
    file_handler.setLevel(DEBUG)
    file_handler.setFormatter(formatter)

    logger.addHandler(stream_handler)
    logger.addHandler(file_handler)

    logger.debug('track:{}, indicators:{}'.format(args.track, args.indicators))
    print('track:{}, indicators:{}'.format(args.track, args.indicators))
    main(args)
