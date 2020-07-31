# coding: utf-8
import math
import os
import csv
import copy 
import time
import statistics

import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from logging import getLogger
from functools import wraps
from tqdm import tqdm
from scipy.stats import kde
import warnings

import indicator_utils


tqdm.pandas()
logger = getLogger("__main__").getChild("indicator_evaluation")
warnings.filterwarnings('ignore')

class CalcIndicator(object):
    def CE_calculation(self, tra_data, eval_point_outof_bup):
        '''
        Calculate Circular Error (CE)

        Parameters
        ----------
        tra_data : DataFrame
            columns = ['unixtime', 'x_position_m', 'y_position_m']
        eval_point_outof_bup : DataFrame
            evaluation poins out of bup, columns = ['unixtime', 'x_position_m', 'y_position_m'] 
        
        Returns
        -------
        CE_list : list of float
        '''

        logger.debug('Calculate Circular Error (CE) START')

        # Calculate euclidean distance
        def Calc_CE(row):
            try:
                diff_abs = np.abs(np.full(len(tra_data), row['unixtime']) - tra_data['unixtime'])
                min_index = diff_abs.argmin()
                error_m_value = math.hypot(row['x_position_m'] - tra_data['x_position_m'][min_index], 
                                        row['y_position_m'] - tra_data['y_position_m'][min_index])
                return error_m_value
            
            except ValueError:
                return 'error'
        
        CE_list = eval_point_outof_bup.apply(Calc_CE, axis=1).values
        CE_list = [num for num in CE_list if num != 'error']
        CE_list.sort() 
        
        logger.debug('CE:{}'.format(CE_list))
        logger.debug('Calculate Circular Error(CE) END')
        
        return CE_list

    def EAG_calculation(self, tra_data, ref_point, eval_point_between_bup):
        '''
        Calculate Error Accumulation Gradient (EAG)

        Parameters
        ----------
        tra_data : DataFrame
            columns = ['unixtime', 'x_position_m', 'y_position_m']
        ref_point : DataFrame 
            groudtruth point data for evaluation 
        eval_point_between_bup : DataFrame
            evaluation poins between bup, columns = ['unixtime', 'x_position_m', 'y_position_m']

        Returns
        -------
        EAG_list : list of float

        '''

        logger.debug('Calculate Error Accumulation Gradient (EAG) START')   

        # Calculate unixtime absolute error between reference point and evaluation point between BUP
        def unixtime_delta_min(x):
            delta_t_list = abs(np.full(len(ref_point), x) - ref_point['unixtime'])
            delta_t_min = min(delta_t_list)
            return delta_t_min

        ans_point_delta_t = eval_point_between_bup['unixtime'].apply(lambda x : unixtime_delta_min(x)) 
        def Calc_EAG(row):
            try:
                diff_abs = np.abs(np.full(len(tra_data), row['unixtime']) - tra_data['unixtime'])
                min_index = diff_abs.argmin()
                error_m_s_value = math.hypot(row['x_position_m'] - tra_data['x_position_m'][min_index], row['y_position_m'] - tra_data['y_position_m'][min_index]) / row['delta_t']
                return error_m_s_value
            
            except ValueError:
                return 'error'

        eval_point_between_bup.reset_index(drop=True, inplace=True)
        # Escape pandas SettingwithCopyWarning
        eval_point_between_bup = eval_point_between_bup.copy() 
        eval_point_between_bup['delta_t'] =  ans_point_delta_t.values

        EAG_list = eval_point_between_bup.apply(Calc_EAG, axis=1).values              
        EAG_list = [num for num in EAG_list if num != 'error']
        EAG_list.sort() 
        
        logger.debug('EAG:{}'.format(EAG_list))
        logger.debug('Calculate Error Accumulation Gradient (EAG) END')
        
        return EAG_list

    def CA_2Dhistgram_calculation(self, tra_data, ans_point):
        '''
        Calculate Circular Error Distribution Deviation by 2D histgram (CA)
        
        Parameters
        ----------
        tra_data : DataFrame
            columns = ['unixtime', 'x_position_m', 'y_position_m']
        
        ans_point : DataFrame 
            groudtruth point data for evaluation

        Returns
        ------- 
        CA: float
        fig: matplotlib Figure object 
        '''
        
        def calc_error_dist(tra_data, ans_point):
            def error_m_xy(row):    
                diff_abs = np.abs(np.full(len(tra_data), row['unixtime']) - tra_data['unixtime'])
                min_index = diff_abs.argmin()
                x_error, y_error = row['x_position_m'] - tra_data['x_position_m'][min_index], row['y_position_m'] - tra_data['y_position_m'][min_index]
                return  pd.Series([x_error, y_error])

            result = pd.DataFrame({'x_error':[], 'y_error':[]})
            result[['x_error', 'y_error']] = ans_point.apply(error_m_xy, axis=1)
            return result
    
        error_xy_series = calc_error_dist(tra_data, ans_point)
        
        def calc_2D_histgram_mod(x_error_list, y_error_list):
            
            fig = plt.figure()
            
            plt.rcParams['font.size'] = 12
            xmax = max(np.abs(x_error_list))
            ymax = max(np.abs(y_error_list))

            xbin = math.floor(xmax * 2/0.5)
            ybin = math.floor(ymax * 2/0.5)

            counts, xedges, yedges, _ = plt.hist2d(x_error_list,y_error_list, bins=(xbin, ybin))
            x_delta = xedges[1] - xedges[0]
            y_delta = yedges[1] - yedges[0]
            
            idx = np.unravel_index(np.argmax(counts), counts.shape)
            
            x_mod = xedges[idx[0]] + x_delta/2
            y_mod = yedges[idx[1]] + y_delta/2
            
            plt.plot(x_mod, y_mod, marker='^', color='forestgreen', 
                    markerfacecolor='white', markeredgewidth=2, markersize=12)
            plt.xlabel('X error')
            plt.ylabel('Y error')
            plt.close()
            
            return x_mod, y_mod, fig

        x_mod, y_mod, fig = calc_2D_histgram_mod(error_xy_series['x_error'].to_list(), 
                                                error_xy_series['y_error'].to_list())

        logger.debug('x mod: {}, y mod: {}'.format(x_mod, y_mod))

        CA = math.hypot(x_mod, y_mod)
        
        logger.debug('CA: {}'.format(CA))

        return CA, fig

    def CA_KernelDensity_calculation(self, tra_data, ans_point, band_width=None):
        '''
        Calculate Circular Error Distribution Deviation by kernel density (CA)
        
        Parameters
        ----------
        tra_data : DataFrame
            columns = ['unixtime', 'x_position_m', 'y_position_m']
        
        ans_point : DataFrame 
            groudtruth point data for evaluation

        band_width : float
            bandwdith for kernel denstiy

        Returns
        ------- 
        CA : float 
        fig: matplotlib Figure object 
        '''

        def calc_error_dist(tra_data, ans_point):
            def error_m_xy(row):    
            # Rounded down unixtime
                diff_abs = np.abs(np.full(len(tra_data), row['unixtime']) - tra_data['unixtime'])
                min_index = diff_abs.argmin()
                x_error, y_error = row['x_position_m'] - tra_data['x_position_m'][min_index], row['y_position_m'] - tra_data['y_position_m'][min_index]
                return  pd.Series([x_error, y_error])

            result = pd.DataFrame({'x_error':[], 'y_error':[]})
            result[['x_error', 'y_error']] = ans_point.apply(error_m_xy, axis=1)
            return result
    
        error_xy_series = calc_error_dist(tra_data, ans_point)

        def calc_kernel_density_mod(x, y, bw_method=None):

            fig = plt.figure()
            sns.set_style('whitegrid')
            plt.rcParams['font.size'] = 12
            nbins=300
            k = kde.gaussian_kde([x,y], bw_method=bw_method)
            xi, yi = np.mgrid[min(x)-2:max(x)+2:nbins*1j, min(y)-2:max(y)+2:nbins*1j]
            try:
                zi = k(np.vstack([xi.flatten(), yi.flatten()]))
            except:
                logger.debug('Unable to calculate inverse matrix, return mean value')
                return np.mean(x), np.mean(y), fig

            row_idx = np.argmax(zi) // len(xi)
            col_idx = np.argmax(zi) % len(yi)
            x_mod = xi[:, 0][row_idx].round(2)
            y_mod = yi[0][col_idx].round(2)
            
            plt.pcolormesh(xi, yi, zi.reshape(xi.shape), cmap='jet')
            plt.plot(x_mod, y_mod, marker='^', color='forestgreen', 
                    markerfacecolor='white', markeredgewidth=2, markersize=12)
            plt.title('x: {:.2f} y: {:.2f}'.format(x_mod, y_mod))
            plt.xlabel('X error')
            plt.ylabel('Y error')

            plt.close()

            return x_mod, y_mod, fig

        x_mod, y_mod, fig = calc_kernel_density_mod(error_xy_series['x_error'].to_list(), 
                                                    error_xy_series['y_error'].to_list(), 
                                                    bw_method=band_width)

        logger.debug('x mod: {}, y mod: {}'.format(x_mod, y_mod))

        CA = math.hypot(x_mod, y_mod)
        
        logger.debug('CA: {}'.format(CA))

        return CA, fig

    def Area_weighted_CA_calculation(self, tra_data, evaluation_point, area_info, 
                                    area_weights, use_2d_hist=False, band_width=None):
        '''
        Calculate Area Weighted Circular Error Distribution Deviation 
        
        Parameters
        ---------
        tra_data: DataFrame
            columns = ['unixtime', 'x_position_m', 'y_position_m']
        evaluation_point: DataFrame
            columns = ['unixtime', 'x_position_m', 'y_position_m']
        area_info: DataFrame
            columns = ['area', 'x_position_m', 'y_position_m', 'x_length', 'y_length']
        area_weights: list of float
        use_kde: boolean
        band_width: float

        Returns
        -------
        area_weighted_CA: float
        CA_df: DataFrame, columns = ['area', 'CA']
        fig_list: list of Figure
        '''

        CA_list = []
        area_list = []
        fig_list = []
        for area_num in range(len(area_info)):
            area_eval_point = indicator_utils.filter_area_point(evaluation_point, area_info, area_num+1)
            if len(area_eval_point) == 0:
                CA = 0
                CA_fig = plt.figure()
                plt.close()
                fig_list.append(CA_fig)
            else:
                if use_2d_hist:
                    CA, CA_fig = self.CA_2Dhistgram_calculation(tra_data, area_eval_point)
                else:
                    CA, CA_fig = self.CA_KernelDensity_calculation(tra_data, area_eval_point, band_width=band_width)
                
            CA_list.append(CA)
            area_list.append(area_num+1)
            fig_list.append(CA_fig)

        CA_df = pd.DataFrame({'area': area_list, 
                                'CA': CA_list})
        
        area_weighted_CA = 0
        for weight, CA in zip(area_weights, CA_list):
            area_weighted_CA += weight * CA

       
        return area_weighted_CA, CA_df, fig_list

    def requirement_moving_velocity_check(self, tra_data, appropriate_velocity=1.5):
        '''
        Calculate Requirement for moving velocity

        Parameters
        ----------
        tra_data : DataFrame
            columns = ['unixtime', 'x_position_m', 'y_position_m']
        
        appropriate_velocity : float
            velcotiy (m/s)
        
        Returns
        ------- 
        moving_velocity_check: DataFrame
            columns = ['unixtime', 'velocity', 'flag']
        '''

        logger.debug('Calculate Requirement for moving velocity START')
        logger.debug('Appropriate velocity: {}'.format(appropriate_velocity))

        # Calculate difference between each row
        tra_dif = tra_data.diff()[1:].copy()
        
        velocity_list = np.hypot(tra_dif['x_position_m'], tra_dif['y_position_m']) / tra_dif['unixtime']

        appropriate_list = [int(velocity < appropriate_velocity) for velocity in velocity_list]
        
        moving_velocity_check = pd.DataFrame({'unixtime': tra_data['unixtime'][1:].values,
                                             'velocity': velocity_list,
                                             'flag': appropriate_list})

        moving_velocity_check = moving_velocity_check.reset_index()

        logger.debug('Appropriate velocity count: {}'.format(sum(appropriate_list)))
        logger.debug('Calculate Requirement for moving velocity END')

        return moving_velocity_check

    def requirement_obstacle_check(self, tra_data, obstacle, map_size):
        '''
        Calculate requirement for obstacle avoidance

        Parameters
        ---------- 
        tra_data : DataFrame
            columns = ['unixtime', 'x_position_m', 'y_position_m']
        obstacle : ndarray
            groudtruth obstacle bitmap data 
        map_size : ndarray of float
            map size like [x_length, y_length]
        
        Returns
        ------- 
        obstacle_check: DataFrame
            columns = ['check_cordinate_count', 'obstacle_cordinate_count']
        '''

        logger.debug('Calculate requirement for obstacle avoidance START')

        x_block_m = len(obstacle[0]) / map_size[0]
        y_block_m = len(obstacle) / map_size[1]

        # Convert bitmap coordinate to mapsize coordinate
        tra_data = tra_data.copy()
        tra_data['x_block_num'] = (tra_data['x_position_m'] * x_block_m).map(lambda x: int(x) -1 if int(x)!=0 else 0)

        tra_data['y_block_num'] = ((map_size[1] - tra_data['y_position_m']) * y_block_m).map(lambda x: int(x) -1 if int(x)!=0 else 0)

        dif_tra_data = tra_data.diff()[1:].reset_index(drop=True) # x_block_num_t1 - x_block_num
        dif_tra_data = dif_tra_data.append(pd.Series([0, 0, 0, 0, 0], index=dif_tra_data.columns, name=len(tra_data)-1)) 
        
        tra_data['x_block_num_dif'] = dif_tra_data['x_block_num'].astype(int)
        tra_data['y_block_num_dif'] = dif_tra_data['y_block_num'].astype(int)
        
        # Auxiliary function to calculate E_obstacle
        # check_pattern, is_inside_map, is_obstacle, is_obstacle_around, is_obstacle_exist, 
        # ObstacleCordinate_count, CheckCordinate_count
        def check_pattern(row):
            '''
            Fucntion to calculate obstacle error
            Appoint pattern to trajection point

            Parameters
            ----------
            row : pd.Series
                trajection file row data

            Return
            ------
            pattern : str
                'A' or 'B' or 'C' or 'D'
            '''

            x_dif = row['x_block_num_dif']
            y_dif = row['y_block_num_dif']
            
            if x_dif == 0:
                if y_dif  > 0:
                    return 'A'
                else:
                    return 'B'
        
            else:
                if x_dif > 0:
                    return 'C'
                elif x_dif < 0:
                    return 'D'

        def is_inside_map(x, y):
            '''
            Fucntion to calculate obstacle error
            Check wheather input cordinate is inside bitmap data or not

            Parameters
            ----------
            x, y : int
                Cordinates
            
            Returns
            -------
            boolean : bool
                if cordinate is inside bitmap : True, else :  False
            '''
            if  0 <= x < obstacle.shape[1]  and 0 <= y < obstacle.shape[0]:
                return True
            else:
                return False
            
        def is_obstacle(x, y):
            '''
            Fucntion to calculate obstacle error
            Check wheather obstacle exsits on input cordinates in bitmap data or not
            
            Parameters
            ----------
            x, y : int
                Cordinates
            
            Returns
            -------
            boolean : bool
                if obstacle exists on input cordinates : True, else :  False
            '''
            if obstacle[y][x] == 1:
                return True
            else:
                return False

        def is_obstacle_around(x, y):
            '''
            Fucntion to calculate obstacle error
            Check wheather all area around input cordinates are filled with obstacle or not
            
            Parameters
            ----------
            x, y : int
                Cordinates
            
            Returns
            -------
            boolean : bool
                if no empty point exist : True, else :  False
            '''

            for x_i in range(-3, 4):
                for y_i in range(-3, 4):
                    if is_inside_map(x + x_i, y + y_i):
                        if not is_obstacle(x + x_i, y+y_i):
                            return False          
            return True

        def is_obstacle_exist(x, y):
            '''
            Fucntion to calculate obstacle error
            Check wheather obstacle exist on input cordinate including around area

            Parameters
            ----------
            x, y : int
                Cordinates
            
            Returns
            -------
            boolean : bool
                if obstacle exist on input cordinates: True, else :  False
            '''
            if is_inside_map(x, y):
                if is_obstacle(x, y):
                    if is_obstacle_around(x, y):
                        return True
            return False
        
        def ObstacleCordinate_count(row):
            '''
            Fucntion to calculate obstacle error
            Count total cordinates where obstacle exist in trajection data

            Parameters
            ----------
            row : pd.Series
                trajection file row data
            
            Returns
            -------
            obstacle_count : int
                number of total cordinates where obstacle exist
            '''

            y_block_num = row['y_block_num']
            y_block_num_t1 = y_block_num + row['y_block_num_dif']
            
            x_block_num = row['x_block_num']
            x_block_num_t1 = x_block_num + row['x_block_num_dif']
            
            obstacle_count = 0
            
            if row['pattern'] == 'A':
                for y in range(y_block_num, y_block_num_t1):
                    if is_obstacle_exist(x_block_num, y):
                        obstacle_count += 1

            elif row['pattern'] == 'B':
                for y in range(y_block_num, y_block_num_t1, -1):
                    if is_obstacle_exist(x_block_num, y):
                        obstacle_count += 1
                    
            elif row['pattern'] == 'C':
                a = int((y_block_num - y_block_num_t1) / (x_block_num - x_block_num_t1))
                b = y_block_num - (a * x_block_num)
                for x in range(x_block_num, x_block_num_t1):
                    y = int(a * x + b)
                    if is_obstacle_exist(x, y):
                        obstacle_count += 1
                                        
            elif row['pattern'] == 'D':
                a = int((y_block_num - y_block_num_t1) / (x_block_num - x_block_num_t1))
                b = y_block_num - (a * x_block_num)
                for x in range(x_block_num, x_block_num_t1, -1):
                    y = int(a * x + b)
                    if is_obstacle_exist(x, y):
                        obstacle_count += 1
                
            return obstacle_count

        def CheckCordinate_count(row):
            '''
            Fucntion to calculate obstacle error
            Count total codinates checked wheather obstacle exist or not

            Parameters
            ----------
            row : pd.Series
                trajection file row data
            
            Returns
            -------
            check_cordinate_count : int
                number of total cordinates checked wheather obstacle exist or not
            '''

            pattern = row['pattern']
            if pattern  == 'A' or pattern  == 'B':
                return abs(row['y_block_num_dif'])
            else:
                return abs(row['x_block_num_dif'])
                
        tra_data['pattern'] = tra_data.apply(check_pattern, axis=1)
        
        obstacle_cordinate_count =  tra_data.progress_apply(ObstacleCordinate_count, axis=1)
        check_cordinate_count = tra_data.apply(CheckCordinate_count, axis=1)

        obstacle_check = pd.DataFrame({'check_cordinate_count': list(check_cordinate_count),
                                      'obstacle_cordinate_count': list(obstacle_cordinate_count)})
                
        logger.debug('Calculate requirement for obstacle avoidance END')

        return obstacle_check
        
