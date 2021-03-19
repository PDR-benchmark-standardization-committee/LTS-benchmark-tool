# coding: utf-8
import os 

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
        self.indicator_total = defaultdict(pd.Series)
        self.which_area = pd.DataFrame()
        self.file_indicator = None

    def add_indicator_percentile(self, indicator_name, indicator):
        self.indicator_values[indicator_name].append(indicator)
        
    def add_total_indicator(self, indicator_name, indicator_series):
        self.indicator_total[indicator_name] = pd.concat([self.indicator_total[indicator_name],
                                                          indicator_series], axis=0)

    def add_total_area_info(self, which_area_info):
        self.which_area = pd.concat([self.which_area, which_area_info], axis=0)

    def summarize_file_indicator(self):
        self.file_indicator = pd.DataFrame(self.indicator_values)
        return self.file_indicator

    def summarize_total_indicator(self):
        indicator_summary = pd.DataFrame(self.file_indicator.mean()).T
        for key, indicator in self.indicator_total.items():
            indicator_summary[key] = np.median(indicator)
        return indicator_summary

    def calc_total_indicator_percentile_each_area(self):
        area_indicator = defaultdict(list)
        for area, indicator in zip(self.which_area, self.indicator_total):
            area_indicator[area].append(total)
        area_indicator50 = pd.DataFrame({area: np.median(v) for area, v in area_indicator.items()})
        return area_indicator50


def save_indicator(data, save_dir, save_filename):
    '''
    save CE, EAG as csv

    Paramters
    ---------
    data : list of float
    save_filename : str
    '''
    
    indicator_save_path = os.path.join(save_dir, save_filename)
    data.to_csv(indicator_save_path, index=False)

def area_of_ans(ans_point, area_info):
    '''
    Fucntion to classify each rows of ans_point to area_num

    Parameters
    ----------
    ans_point : pd.DataFrame
    area_info : pd.DataFrame

    Returns
    -------
    which_area_series : pd.Series
        number of area
    '''
    def get_area(row):
        for area_num in range(1, len(area_info)+1):
            target_area_info = area_info[area_info['area']==area_num] 
            x_min = target_area_info['x_position_m'] - target_area_info['x_length']
            x_max = target_area_info['x_position_m'] + target_area_info['x_length']
            y_min = target_area_info['y_position_m'] - target_area_info['y_length']
            y_max = target_area_info['y_position_m'] + target_area_info['y_length']

            if x_min.values[0] <= row['x_position_m'] <= x_max.values[0] \
                and y_min.values[0] <= row['y_position_m'] <= y_max.values[0]:
                return area_num
        return 0
    which_area_series = ans_point.apply(get_area, axis=1)
    return which_area_series 
    
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

def draw_trajectory(tra_data, map_image, map_size, indicator_name, ref_point, BLE_info):
    '''
    draw trajectory on maps

    Parameters
    ----------
    tra_data : list of float
    map_image : bitmap
    map_size : float
    '''

    fig = plt.figure(dpi=600)
    plt.imshow(map_image, extent=[0, map_size[0], 0, map_size[1]], cmap='gist_gray')
    plt.plot(tra_data['x_position_m'], tra_data['y_position_m'], color='red', lw=0.2, label='Trajectory')
    plt.plot(ref_point['x_position_m'], ref_point['y_position_m'], color='yellow', linestyle='None', marker='+', markersize='0.3', label='Reference')
    plt.plot(BLE_info['x_position_m'], BLE_info['y_position_m'], color='orange', linestyle='None', marker='.', markersize='0.5', label='BLE')
    plt.title(f'{indicator_name}')
    plt.xlabel('x [m]')
    plt.ylabel('y [m]')
    plt.legend(fontsize='small')
    
    return fig

def draw_CE_map(indicator_df, map_image, map_size, indicator_name):
    '''
    draw CE on maps

    Parameters
    ----------
    tra_data : list of float
    map_image : bitmap
    map_size : float
    '''
    import matplotlib.cm as cm
    import matplotlib.colors as colors
    cmap = cm.cool
    cmap_data = cmap(np.arange(cmap.N))
    cmap_data[0, 3] = 0 # 0 のときのα値を0(透明)にする
    customized_cool = colors.ListedColormap(cmap_data)

    fig = plt.figure(dpi=600)
    #ax = fig.add_subplot(111)
    ax = fig.add_axes((0.05, 0.05, 0.8, 0.9))

    ax.imshow(map_image, extent=[0, map_size[0], 0, map_size[1]])

    error_map = calc_CE_map(indicator_df, map_size)
    X, Y = np.mgrid[0:error_map.shape[0], 0:error_map.shape[1]]
    im = ax.pcolormesh(X, Y, error_map, cmap=customized_cool)

    cax = fig.add_axes((0.9, 0.15, 0.03, 0.7))
    plt.colorbar(im, cax=cax)

    ax.set_title(f'{indicator_name}_error_map')
    ax.set_xlabel('x [m]')
    ax.set_ylabel('y [m]')
    
    return fig

def calc_CE_map(indicator_df, map_size, cell_size=1.0):
    error_map_x = int(map_size[0] / cell_size)
    error_map_y = int(map_size[1] / cell_size)
    error_sum_map = np.zeros((error_map_x, error_map_y))
    error_count_map = np.zeros((error_map_x, error_map_y))

    def add_error(row):
        error_x = int(row['eval_x'] / cell_size)
        error_y = int(row['eval_y'] / cell_size)
        error_sum_map[error_x, error_y] += row['CE']
        error_count_map[error_x, error_y] += 1
    
    indicator_df.apply(add_error, axis=1)

    # avoid division by zero
    error_count_map += 1e-8
    error_map = error_sum_map / error_count_map

    return error_map
