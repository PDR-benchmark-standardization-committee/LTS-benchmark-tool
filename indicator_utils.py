# coding: utf-8
import os 

import cv2
from collections import defaultdict
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from logging import getLogger

logger = getLogger("__main__").getChild("indicator utility")

class IndicatorHolder(object):
    def __init__(self): 
        self.indicator_values = defaultdict(list)
        self.file_indicator = None

    def add_indicator(self, indicator_name, indicator):
        self.indicator_values[indicator_name].append(indicator)
        
    def summarize_file_indicator(self):
        self.file_indicator = pd.DataFrame(self.indicator_values)
        return self.file_indicator

    def calc_total_indicator(self, CE_total, EAG_total):
        total_indicator = pd.DataFrame(self.file_indicator.mean()).T
        total_indicator['CE50'] = np.median(CE_total)
        total_indicator['EAG50'] = np.median(EAG_total)
        return total_indicator

def save_indicator(data, indicator_name, save_dir, save_filename):
    '''
    save CE, EAG as csv

    Paramters
    ---------
    data : list of float
    save_filename : str
    '''
    
    indicator_save_path = os.path.join(save_dir, save_filename)

    save_df = pd.DataFrame({indicator_name : data})
    save_df.to_csv(indicator_save_path, index=False)
    logger.debug('save {} at {}'.format(indicator_name, indicator_save_path))

def save_indicator_debug(data, save_dir, save_filename):
    '''
    save CE, EAG as csv

    Paramters
    ---------
    data : list of float
    save_filename : str
    '''
    
    indicator_save_path = os.path.join(save_dir, save_filename)

    data.to_csv(indicator_save_path, index=False)

def draw_cumulative_sum(data, indicator_name):
    '''
    draw cumulative sum of EAG and CE
    
    Parameters
    ----------
    data : list of float
    indicator_name : str
    '''

    eCDF_plus = 100 / len(data)
    eCDF = [eCDF_plus]
    for i in range(len(data)-1):
        eCDF.append(eCDF[i] + eCDF_plus)

    data.sort()

    fig = plt.figure()
    sns.set_style('whitegrid')
    plt.plot(data, eCDF)
    plt.title(f'{indicator_name}')
    if indicator_name is 'CE':
        plt.xlabel(f'{indicator_name} [m]')
    elif indicator_name is 'EAG':
        plt.xlabel(f'{indicator_name} [m/s]')
    plt.ylabel('eCDF')

    plt.close()

    return fig

def draw_histgram(data, indicator_name, percentile=50, bins=None):
    '''
    draw histgram of EAG and CE

    Parameters
    ----------
    data : list of float
    bins : int
    '''

    logger.debug('draw histgram')
    fig = plt.figure()
    sns.set_style('whitegrid')
    plt.rcParams['font.size'] = 12 
    percentile_value = calc_percentile(data, percentile)
    sns.distplot(data, kde=False, rug=False, bins=bins)
    plt.axvline(percentile_value, color='k', linestyle='dashed', linewidth=1)
    plt.title(f'{indicator_name}{percentile}: {percentile_value:.2f}')
    plt.xlabel(f'{indicator_name}')
    plt.ylabel('Frequency')

    plt.close()

    return fig
    
def calc_percentile(data, percentile):
    if percentile < 0 or 100 < percentile:
        raise ValueError('percentile shoud be between 0 and 1')
    return np.percentile(data, q=percentile)
    
def save_figure(figure, save_dir, save_filename):
    fig_save_path = os.path.join(save_dir, save_filename)
    figure.savefig(fig_save_path)
    logger.debug('save figure at {}'.format(fig_save_path))

def save_total_indicator(data, indicator_name, save_dir, save_filename):
    save_path = os.path.join(save_dir, save_filename)
    save_df = pd.DataFrame({indicator_name : data})
    save_df.to_csv(save_path, index=False)
    logger.debug('save at {}'.format(save_path))

def save_dataframe(save_dir, save_filename, df):
    save_path = os.path.join(save_dir, save_filename)
    df.to_csv(save_path, index=False)

def filter_area_point(evaluation_point, area_info, area_num):
    '''
    Get evaluation point inside target area

    Parameters
    ----------
    evaluation_point: DataFrame
        columns = ['unixtime', 'x_position_m', 'y_position_m']
    area_info: DataFrame
        columns = ['area', 'x_position_m', 'y_position_m', 'x_length', 'y_length']
    area_num: int
        target area number
    '''
    
    logger.debug('Get area {} evaluation point START'.format(area_num))

    target_area_info = area_info[area_info['area']==area_num] 
    x_min = target_area_info['x_position_m'] - target_area_info['x_length']
    x_max = target_area_info['x_position_m'] + target_area_info['x_length']
    y_min = target_area_info['y_position_m'] - target_area_info['y_length']
    y_max = target_area_info['y_position_m'] + target_area_info['y_length']

    area_eval_point = evaluation_point.query(f'{x_min.values[0]} < x_position_m < {x_max.values[0]}')

    area_eval_point = area_eval_point.query(f'{y_min.values[0]} < y_position_m < {y_max.values[0]}')
    
    logger.debug('Get area {} evaluation point END, area_eval_point:{}'.\
                format(area_num, area_eval_point.shape))
    return area_eval_point

def get_CA_area_weights(evaluation_point, area_info):
    '''
    calculate CA area weights

    Parameters
    ------
    evaluation_point: DataFrame 
        columns = ['unixtime', 'x_position_m', 'y_position_m']
    area_info: DataFrame
        columns = ['area', 'x_position_m', 'y_position_m', 'x_length', 'y_length']

    Return
    ------
    weights: list of float
        ratio of area's evaluation points in whole area evaluation points
    '''

    logger.debug('calculate CA area weights START')

    if area_info is None:
        return None

    area_point_counts = []
    for area_num in range(len(area_info)):
        area_eval_point = filter_area_point(evaluation_point, area_info, area_num+1)
        area_point_counts.append(len(area_eval_point))
    
    total_points = sum(area_point_counts)
    weights = [area_point / total_points for area_point in area_point_counts]
    
    logger.debug('calculate EDD area weights END, weight: {}'.format(weights))
    
    return weights

def draw_trajectory(tra_data, map_image, map_size, indicator_name, ref_point, ble_info, map_color, map_makersize):
    '''
    draw trajectory on maps

    Parameters
    ----------
    tra_data : list of float
    map_image : bitmap
    map_size : float
    '''

    fig = plt.figure(dpi=600)
    map_image2 = cv2.bitwise_not(map_image)
    plt.imshow(map_image2, cmap=map_color[0], extent=[0, map_size[0], 0, map_size[1]])
    plt.plot(tra_data['x_position_m'], tra_data['y_position_m'], color=map_color[1], lw=map_makersize[0], label='Trajectory')
    plt.plot(ref_point['x_position_m'], ref_point['y_position_m'], color=map_color[2], linestyle='None', marker='+', markersize=map_makersize[1], label='Reference')
    plt.plot(ble_info['x_position_m'], ble_info['y_position_m'], color=map_color[3], linestyle='None', marker='.', markersize=map_makersize[2], label='BLE')
    plt.title(f'{indicator_name}')
    plt.xlabel('x [m]')
    plt.ylabel('y [m]')
    plt.legend(fontsize='small')
    
    return fig
