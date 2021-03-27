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
    def extract_correspond_point(self, tra_point, eval_point, sec_limit=1.0):

        '''
        extract correspond point from tra_point

        Parameters
        ----------
        tra_point : DataFrame
            columns = ['unixtime', 'x_position_m', 'y_position_m']
        eval_point_ALAP : DataFrame
            evaluation points in ALAP, columns = ['unixtime', 'x_position_m', 'y_position_m'] 
        sec_limit : float
            match time limit [sec]
        
        Returns
        -------
        correspond_df : DataFrame
            columns = ['unixtime', 'tra_x', 'tra_y', 'eval_x', 'eval_y', 'correspond_time']
        '''
        # Calculate euclidean distance
        unixtime_list = []
        tra_x_list = []
        tra_y_list = []
        eval_x_list = []
        eval_y_list = []
        correspond_time_list = []

        def Calc_correspond(row):
            try:
                diff_abs = np.abs(np.full(len(tra_point), row['unixtime']) - tra_point['unixtime'])
                min_index = diff_abs.argmin()

                if diff_abs[min_index] <= sec_limit:
                    unixtime_list.append(row['unixtime'])
                    tra_x_list.append(tra_point['x_position_m'][min_index])
                    tra_y_list.append(tra_point['y_position_m'][min_index])
                    eval_x_list.append(row['x_position_m'])
                    eval_y_list.append(row['y_position_m'])
                    correspond_time_list.append(diff_abs[min_index])
                else: #no match
                    logger.debug('warning : no match traj_point and eval_point at unixtime {}'.format(row['unixtime']))
            
            except ValueError:
                logger.debug('warning : value error occurred at unixtime {}'.format(row['unixtime']))

        eval_point.apply(Calc_correspond, axis=1).values
        correspond_df = pd.DataFrame({'unixtime' : unixtime_list,
                              'tra_x' : tra_x_list,
                              'tra_y' : tra_y_list,
                              'eval_x' : eval_x_list,
                              'eval_y' : eval_y_list,
                              'correspond_time' : correspond_time_list})
        return correspond_df

    def CE_calculation(self, tra_point, eval_point_ALAP):
        '''
        Calculate Circular Error (CE)

        Parameters
        ----------
        tra_point : DataFrame
            columns = ['unixtime', 'x_position_m', 'y_position_m']
        eval_point_ALAP : DataFrame
            evaluation points in ALAP, columns = ['unixtime', 'x_position_m', 'y_position_m'] 
        
        Returns
        -------
        CE_df : DataFrame
            columns = ['unixtime', 'tra_x', 'tra_y', 'eval_x', 'eval_y', 'correspond_time', 'CE']
        '''

        logger.debug('Calculate Circular Error (CE) START')

        correspond_df = self.extract_correspond_point(tra_point, eval_point_ALAP)

        def Calc_CE(row):
            error_m_value = math.hypot(row['tra_x'] - row['eval_x'], row['tra_y'] - row['eval_y'])
            return error_m_value
        
        correspond_df['CE'] = correspond_df.apply(Calc_CE, axis=1)
        logger.debug('Calculate Circular Error(CE) END')
        return correspond_df

    def EAG_calculation(self, tra_point, ref_point, eval_point_ALIP):
        '''
        Calculate Error Accumulation Gradient (EAG)

        Parameters
        ----------
        tra_point : DataFrame
            columns = ['unixtime', 'x_position_m', 'y_position_m']
        ref_point : DataFrame 
            groudtruth point data for evaluation 
        eval_point_ALIP : DataFrame
            evaluation poins in ALIP, columns = ['unixtime', 'x_position_m', 'y_position_m']

        Returns
        -------
        EAG_df : DataFrame
            columns = ['unixtime', 'tra_x', 'tra_y', 'eval_x', 'eval_y', 'correspond_time', 'EAG', 'delta_t']

        '''

        logger.debug('Calculate Error Accumulation Gradient (EAG) START')   

        # Calculate unixtime absolute error between reference point and evaluation point in ALIP
        def unixtime_delta_min(x):
            delta_t_list = abs(np.full(len(ref_point), x) - ref_point['unixtime'])
            delta_t_min = min(delta_t_list)
            return delta_t_min

        correspond_df = self.extract_correspond_point(tra_point, eval_point_ALIP)
        eval_point_delta_t = correspond_df['unixtime'].apply(lambda x : unixtime_delta_min(x))

        correspond_df.reset_index(drop=True, inplace=True)
        # Escape pandas SettingwithCopyWarning
        correspond_df = correspond_df.copy() 
        correspond_df['delta_t'] = eval_point_delta_t.values

        def Calc_EAG(row):
            error_m_value = math.hypot(row['tra_x'] - row['eval_x'], row['tra_y'] - row['eval_y']) / row['delta_t']
            return error_m_value

        correspond_df['EAG'] = correspond_df.apply(Calc_EAG, axis=1)
        logger.debug('Calculate Error Accumulation Gradient (EAG) END')
        return correspond_df

    def CP_calculation(self, tra_point, eval_point, band_width=None):
        '''
        Calculate Calculate Circular Presicion(CP)
        
        Parameters
        ----------
        tra_point : DataFrame
            columns = ['unixtime', 'x_position_m', 'y_position_m']
        
        eval_point : DataFrame 
            groudtruth point data for evaluation

        Returns
        ------- 
        CP_df : DataFrame
            columns = ['unixtime', 'CP', 'correspond_time']
        '''
        logger.debug('Calculate Calculate Circular Presicion(CP) START')   

        correspond_df = self.extract_correspond_point(tra_point, eval_point)

        error_xy_series = self.calc_error_dist(tra_point, eval_point)
        xi, yi, zi = self.calc_kernel_density(error_xy_series['x_error'].to_list(), 
                                                error_xy_series['y_error'].to_list(), 
                                                bw_method=band_width)
        x_mod, y_mod = self.calc_density_mode(xi, yi, zi)

        def Calc_CP(row):
            error_x = row['tra_x'] - row['eval_x']
            error_y = row['tra_y'] - row['eval_y']
            error_dist_value = math.hypot(error_x - x_mod, error_y - y_mod)
            return error_dist_value

        correspond_df['CP'] = correspond_df.apply(Calc_CP, axis=1)
        
        logger.debug('Calculate Presicion Error(CP) END')
        return correspond_df
    
    def calc_error_dist(self, tra_point, eval_point):

        correspond_df = self.extract_correspond_point(tra_point, eval_point)
        def error_m_xy(row):    
            x_error, y_error = row['tra_x'] - row['eval_x'], row['tra_y'] - row['eval_y']
            return  pd.Series([x_error, y_error])

        result = pd.DataFrame({'x_error':[], 'y_error':[]})
        result[['x_error', 'y_error']] = correspond_df.apply(error_m_xy, axis=1)
        return result
    
    def CA_2Dhistgram_calculation(self, tra_point, eval_point):
        '''
        Calculate Circular Error Distribution Deviation by 2D histgram (CA)
        
        Parameters
        ----------
        tra_point : DataFrame
            columns = ['unixtime', 'x_position_m', 'y_position_m']
        
        eval_point : DataFrame 
            groudtruth point data for evaluation

        Returns
        ------- 
        CA: float
        fig: matplotlib Figure object 
        '''
        
        error_xy_series = self.calc_error_dist(tra_point, eval_point)
        
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

    def CA_KernelDensity_calculation(self, tra_point, eval_point, band_width=None):
        '''
        Calculate Circular Error Distribution Deviation by kernel density (CA)
        
        Parameters
        ----------
        tra_point : DataFrame
            columns = ['unixtime', 'x_position_m', 'y_position_m']
        
        eval_point : DataFrame 
            groudtruth point data for evaluation

        band_width : float
            bandwdith for kernel denstiy

        Returns
        ------- 
        CA : float 
        fig: matplotlib Figure object 
        '''

        error_xy_series = self.calc_error_dist(tra_point, eval_point)
        
        xi, yi, zi = self.calc_kernel_density(error_xy_series['x_error'].to_list(), 
                                                error_xy_series['y_error'].to_list(), 
                                                bw_method=band_width)
        x_mod, y_mod = self.calc_density_mode(xi, yi, zi)
        fig = self.figure_density(xi, yi, zi, x_mod, y_mod)

        logger.debug('x mod: {}, y mod: {}'.format(x_mod, y_mod))
        
        CA = math.hypot(x_mod, y_mod)
        
        logger.debug('CA: {}'.format(CA))
        
        return CA, fig

    def calc_kernel_density(self, x, y, bw_method=None):

        nbins=300
        k = kde.gaussian_kde([x,y], bw_method=bw_method)
        xi, yi = np.mgrid[min(x)-2:max(x)+2:nbins*1j, min(y)-2:max(y)+2:nbins*1j]
        try:
            zi = k(np.vstack([xi.flatten(), yi.flatten()]))
        except:
            logger.debug('Unable to calculate inverse matrix, return mean value')
            return np.mean(x), np.mean(y)
        return xi, yi, zi
    
    def calc_density_mode(self, xi, yi, zi):
        row_idx = np.argmax(zi) // len(xi)
        col_idx = np.argmax(zi) % len(yi)
        x_mod = xi[:, 0][row_idx].round(2)
        y_mod = yi[0][col_idx].round(2)
        return x_mod, y_mod

    def figure_density(self, xi, yi, zi, x_mod, y_mod):
        fig = plt.figure()
        sns.set_style('whitegrid')
        plt.rcParams['font.size'] = 12

        plt.pcolormesh(xi, yi, zi.reshape(xi.shape), cmap='jet')
        plt.plot(x_mod, y_mod, marker='^', color='forestgreen', 
                markerfacecolor='white', markeredgewidth=2, markersize=12)
        plt.title('x: {:.2f} y: {:.2f}'.format(x_mod, y_mod))
        plt.xlabel('X error')
        plt.ylabel('Y error')

        plt.close()
        
        return fig

    def Area_weighted_CA_calculation(self, tra_point, eval_point, area_info, 
                                    area_weights, use_2d_hist=False, band_width=None):
        '''
        Calculate Area Weighted Circular Error Distribution Deviation 
        
        Parameters
        ---------
        tra_point: DataFrame
            columns = ['unixtime', 'x_position_m', 'y_position_m']
        eval_point: DataFrame
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
            area_eval_point = indicator_utils.filter_area_point(eval_point, area_info, area_num+1)
            if len(area_eval_point) == 0:
                CA = 0
                CA_fig = plt.figure()
                plt.close()
                fig_list.append(CA_fig)
            else:
                if use_2d_hist:
                    CA, CA_fig = self.CA_2Dhistgram_calculation(tra_point, area_eval_point)
                else:
                    CA, CA_fig = self.CA_KernelDensity_calculation(tra_point, area_eval_point, band_width=band_width)

            CA_list.append(CA)
            area_list.append(area_num+1)
            fig_list.append(CA_fig)

        CA_df = pd.DataFrame({'area': area_list, 
                                'CA': CA_list})
        
        area_weighted_CA = 0
        for weight, CA in zip(area_weights, CA_list):
            area_weighted_CA += weight * CA

       
        return area_weighted_CA, CA_df, fig_list

    def requirement_moving_velocity_check(self, tra_point, appropriate_velocity=1.5):
        '''
        Calculate Requirement for moving velocity

        Parameters
        ----------
        tra_point : DataFrame
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
        tra_dif = tra_point.diff()[1:].copy()
        
        velocity_list = np.hypot(tra_dif['x_position_m'], tra_dif['y_position_m']) / tra_dif['unixtime']

        appropriate_list = [int(velocity < appropriate_velocity) for velocity in velocity_list]
        
        moving_velocity_check = pd.DataFrame({'unixtime': tra_point['unixtime'][1:].values,
                                             'velocity': velocity_list,
                                             'flag': appropriate_list})

        moving_velocity_check = moving_velocity_check.reset_index()

        logger.debug('Appropriate velocity count: {}'.format(sum(appropriate_list)))
        logger.debug('Calculate Requirement for moving velocity END')

        return moving_velocity_check

    def requirement_obstacle_check(self, tra_point, obstacle, map_size):
        '''
        Calculate requirement for obstacle avoidance

        Parameters
        ---------- 
        tra_point : DataFrame
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
        tra_point = tra_point.copy()
        tra_point['x_block_num'] = (tra_point['x_position_m'] * x_block_m).map(lambda x: int(x) -1 if int(x)!=0 else 0)

        tra_point['y_block_num'] = ((map_size[1] - tra_point['y_position_m']) * y_block_m).map(lambda x: int(x) -1 if int(x)!=0 else 0)

        dif_tra_point = tra_point.diff()[1:].reset_index(drop=True) # x_block_num_t1 - x_block_num
        dif_tra_point = dif_tra_point.append(pd.Series([0, 0, 0, 0, 0], index=dif_tra_point.columns, name=len(tra_point)-1)) 
        
        tra_point['x_block_num_dif'] = dif_tra_point['x_block_num'].astype(int)
        tra_point['y_block_num_dif'] = dif_tra_point['y_block_num'].astype(int)
        
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
                
        tra_point['pattern'] = tra_point.apply(check_pattern, axis=1)
        
        obstacle_cordinate_count =  tra_point.progress_apply(ObstacleCordinate_count, axis=1)
        check_cordinate_count = tra_point.apply(CheckCordinate_count, axis=1)

        obstacle_check = pd.DataFrame({'check_cordinate_count': list(check_cordinate_count),
                                      'obstacle_cordinate_count': list(obstacle_cordinate_count)})
                
        logger.debug('Calculate requirement for obstacle avoidance END')

        return obstacle_check
