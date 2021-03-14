# coding: utf-8
import os
import sys

import cv2
import pandas as pd
import numpy as np
from configparser import ConfigParser
from logging import getLogger


logger = getLogger("__main__").getChild("dataloader")


def config(track, base_dname, config_file='config.ini'):
    '''
    Load ground_truth directory ini file

    Parameters
    ----------
    track : str 
        'VDR' or 'PDR'
    config_file : str
        Loading configuration file name
    
    Retruns
    -------
    conf : dictionary
    '''
    logger.debug('Loading configuration file: {}'.format(config_file))

    if not os.path.exists(config_file):
        raise FileExistsError('{} does not exist'.format(config_file))

    # Load ini file
    config_ini = ConfigParser()
    config_ini.optionxform = str
    config_ini.read(config_file, encoding='utf-8')
    conf = dict()

    ini_names ={'dir_name':['map_dname', 'ans_dname', 'ref_dname', 'ALIP_dname', 'BLE_dname'],
                'file_name':['map_image_fname', 'map_size_fname', 'area_fname', 
                            'ref_fname', 'ans_fname', 'ALIP_info_fname', 'BLE_info_fname']}

    for key, values in ini_names.items():
        for v in values:
            item = config_ini[track][v].strip("'")
            if key == 'dir_name':
                item = os.path.join(base_dname, item)
            
            conf[v] = item
            logger.debug('{}: {}'.format(v, item))

    print(conf)
    logger.debug("Configuration file load complete!")
    return conf

def map_size(base_dname, map_size_fname):
    '''
    Load map size file

    Parameters
    ----------
    base_dname : str
    map_size_fname : str
    
    Returns
    -------
    map_size : ndarray of float
        map size [x, y]
    '''
    map_size_path = os.path.join(base_dname, map_size_fname)
    logger.debug('Loading Map size file : {}'.format(map_size_path))
    
    try:
        map_size_df = pd.read_csv(map_size_path, names=['x[m]', 'y[m]'])
    except FileNotFoundError:
        logger.debug('{} does not exists'.format(map_size_path))
        return None

    map_size = map_size_df.values[0]

    logger.debug('Map size load complete! map size: {}'.format(map_size))

    return map_size

def map_image(base_dname, map_image_fname):
    '''
    load map bitmap image

    Parameters
    ----------
    base_dname : str
    map_image_fname : str
    
    Returns
    -------
    bitmap : ndarray of int
        bitmap data 
    '''

    map_image_path = os.path.join(base_dname, map_image_fname)
    logger.debug('Loading map image : {}'.format(map_image_path))

    map_img = cv2.imread(map_image_path, cv2.IMREAD_GRAYSCALE)
    
    # Value 1 is obstacle 
    bitmap = np.where(map_img==255, 0, 1)
    logger.debug('map image load complete! image shape:{}'.format(bitmap.shape))

    return bitmap 

def load_point(base_dname, point_fname):
    '''
    Load point data file

    Parameters
    ----------
    base_dname : str
    point_fname : str
    
    Returns
    -------
    point : DataFrame
        columns = ['unixtime', 'x_position_m', 'y_position_m']
    '''
    point_path = os.path.join(base_dname, point_fname)
    logger.debug('Loading point data: {}'.format(point_path))

    try:
        point = pd.read_csv(point_path, names=['unixtime', 'x_position_m', 'y_position_m'])
    except FileNotFoundError:
        logger.debug('{} does not exists'.format(point_path))
        return None
    
    logger.debug('Point data load complete! columns:{}, shape:{}'.\
        format(point.columns, point.shape))
    
    return point

def ALIP_info(base_dname, ALIP_info_fname):
    '''
    Load true ALIP info file

    Parameters
    ----------
    base_dname : str
    ALIP_info_fname : str
    
    Returns
    -------
    ALIP_info : DataFrame
        columns = ['ALIP_start', 'ALIP_end']
    '''
    ALIP_info_path = os.path.join(base_dname, ALIP_info_fname)
    logger.debug('Loading ALIP info :{}'.format(ALIP_info_path))

    try:
        ALIP_info = pd.read_csv(ALIP_info_path)
    except FileNotFoundError:
        logger.debug('{} does not exist'.format(ALIP_info_path))
        return None
    
    ALIP_info.columns = ['ALIP_start', 'ALIP_end']

    logger.debug('ALIP info load complete! columns:{}, shape:{}'.\
            format(ALIP_info.columns, ALIP_info.shape))
    return ALIP_info

def area_info(base_dname, area_fname):
    '''
    Area info files
    
    Parameters
    ----------
    base_dname : str
    area_fname : str

    Returns
    -------
    area_info : DataFrame
        DataFrame columns = ['area', 'x_position_m', 'y_position_m', 'x_length', 'y_length']
    '''
    area_info_path = os.path.join(base_dname, area_fname)
    logger.debug('Loading Area info file:{}'.format(area_info_path))
    
    try:
        area_info = pd.read_csv(area_info_path)
    except FileNotFoundError:
        logger.debug('{} does not exist'.format(area_info_path))
        return None

    area_info.columns = ['area', 'x_position_m', 'y_position_m', 'x_length', 'y_length']
    logger.debug('Area info load complete! columns:{}, shape:{}'.\
            format(area_info.columns, area_info.shape))
    
    return area_info

def BLE_info(base_dname, BLE_fname):
    '''
    BLE info files
    
    Parameters
    ----------
    base_dname : str
    BLE_fname : str

    Returns
    -------
    BLE_info : DataFrame
        DataFrame columns = ['mac_address', 'orientation', 'x_position_m', 'y_position_m', 'Ptx', 'Lux']
    '''
    BLE_info_path = os.path.join(base_dname, BLE_fname)
    logger.debug('Loading Area info file:{}'.format(BLE_info_path))
    
    try:
        BLE_info = pd.read_csv(BLE_info_path)
    except FileNotFoundError:
        logger.debug('{} does not exist'.format(BLE_info_path))
        return None

    logger.debug('BLE info load complete! columns:{}'.format(BLE_info.columns))
    
    return BLE_info

def area_weights_config(track, config_file='area_weights_config.ini'):
    '''
    Load area weights configuration file for E_error_deviation
    
    Parameters
    ----------
    track : str 
        'VDR' or 'PDR'
    config_file : str
        area weights configuration file name
    
    Retruns
    -------
    area_weights : list of float
    '''
    logger.debug('Loading area weights configuration file.')
    logger.debug('track: {}, config file: {}'.format(track, config_file))

    if not os.path.exists(config_file):
        logger.error('FileExistsError {} does not exist'.format(config_file))
        return None
        
    config_ini = ConfigParser()
    config_ini.optionxform = str
    config_ini.read(config_file, encoding='utf-8')

    area_weights = list()
    for area, weight in config_ini[track].items():
        logger.debug('{}: {}'.format(area, weight))
        area_weights.append(float(weight))
    
    return area_weights

def drop_ans_duplicated_with_ref(ans_point, ref_point):
    '''
    drop duplicated raw with reference point from answer point

    Parameters
    ----------
    ans_point : DataFrame
        total ground truth point
    ref_point : DataFrame
        reference point which is not for evaluation

    Returns
    -------
    ans_ref_nonduplicated : DataFrame
    '''

    ans_point = ans_point.drop_duplicates()
    ref_point = ref_point.drop_duplicates()

    ref_unixtime = ref_point['unixtime']
    ans_duplicated_ref = ans_point[~ans_point['unixtime'].isin(ref_unixtime)]

    return ans_duplicated_ref

def filter_evaluation_data_ALIP(evaluation_point, ALIP_info, ALIP_flag):
    '''
    Filter data between ALIP or not

    Parameters
    ----------
    evaluation_point: DataFrame
        DataFrame columns = ['unixtime', 'x_position_m', 'y_position_m']
    ALIP_info : DataFrame
        ALIP period time information
    ALIP_flag : boolean
        filter point is between ALIP or not

    Returns
    -------
    eval_point : DataFrame
        evaluation point for indicator
    '''
    # Check weather unixtime is between start and end time of ALIP_info
    def is_unixtime_between_ALIP(x):
        for ALIP_start, ALIP_end in zip(ALIP_info['ALIP_start'].values, ALIP_info['ALIP_end'].values):
            if ALIP_start<= x <=ALIP_end:
                return True
        return False
    
    if ALIP_flag:
        # Boolean array
        is_unixtime_between_ALIPinfo = evaluation_point['unixtime'].apply(lambda x:is_unixtime_between_ALIP(x))
        eval_point = evaluation_point[is_unixtime_between_ALIPinfo]
        logger.debug('evaluation point BETWEEN ALIP period is selected')

    else:
        is_unixtime_out_of_ALIPinfo = [not i for i in evaluation_point['unixtime'].apply(lambda x:is_unixtime_between_ALIP(x))]
        eval_point = evaluation_point[is_unixtime_out_of_ALIPinfo]
        logger.debug('evaluation point OUT OF ALIP period is selected')
    
    return eval_point

