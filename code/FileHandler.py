'''
*********************FileHandler.py***********************
includes functions for handling (saving/loading) fits files

@author: siavashyasini
'''

import numpy as np
from astropy.io import fits
import os
from cosmoboost import DEFAULT_PARS
from cosmoboost import COSMOBOOST_DIR
import warnings



def dirname(beta,lmax):
    '''returns the local directory address where the fits file should be saved'''
    return  COSMOBOOST_DIR+"/data/beta_"+str(beta)[2:]+"/lmax_"+str(lmax)


def kernel_filename(s,delta_ell,beta,lmax):
    '''returns the name and address of the fits file based on params'''
    return dirname(beta,lmax)+"/K_d=1_s="+str(s)+"_delta"+str(delta_ell)+"_lmax"+str(lmax)+"_beta"+str(beta)[2:]+".fits"

def matrices_filename(s,delta_ell,beta,lmax):
    '''returns the name and address of the fits file based on params'''
    return dirname(beta,lmax)+"/M_d=1_s="+str(s)+"_delta"+str(delta_ell)+"_lmax"+str(lmax)+"_beta"+str(beta)[2:]+".fits"


def init_kernel_fits(kernel_file_name):
    '''initialize a fits file with 5 HDUs in the following order:
    PRIMARY (T): the aberration kernel matrix for T
    E : the aberration kernel matrix for polarization E mode
    B : the aberration kernel matrix for polarization B mode
    SP2 : the aberration kernel matrix for polarization s = +2
    SM2 : the aberration kernel matrix for polarization s = -2
    '''
    
    #setup all 6 HDUs with their respective keywords
    #*note that the keyword for the aberration kernel matrix is "primary"
    T_hdu = fits.PrimaryHDU()
    T_hdu.name = "T"
    E_hdu = fits.ImageHDU(name="E")
    B_hdu = fits.ImageHDU(name="B")
    SP2_hdu = fits.ImageHDU(name="SP2")
    SM2_hdu = fits.ImageHDU(name="SM2")
    
    hdus = [T_hdu,E_hdu,B_hdu,SP2_hdu,SM2_hdu]
    
    #concatenate the HDUs into an HDUList and write to fits file
    hdulist = fits.HDUList(hdus)
    hdulist.writeto(str(kernel_file_name),overwrite=True)

def init_matrices_fits(matrices_file_name):
    '''initialize a fits file with 6 HDUs in the following order:
        PRIMARY (M): Mmatrix used in doppler weight lifting of the kernel matrix
        Lp: Lpmatrix used in doppler weight lifting of the kernel matrix
        L : Lmatrix used in doppler weight lifting of the kernel matrix
        CS0 : Clm matrix for s=0.
        CS2: Clm matrix for s=2.
        '''
    
    #setup all 6 HDUs with their respective keywords
    #*note that the keyword for the aberration kernel matrix is "primary"
    M_hdu = fits.PrimaryHDU()
    M_hdu.name = "M"
    LP_hdu = fits.ImageHDU(name="LP")
    L_hdu = fits.ImageHDU(name="L")
    CS0_hdu = fits.ImageHDU(name="CS0")
    CS2_hdu = fits.ImageHDU(name="CS2")
    S_hdu = fits.ImageHDU(name="S")
    
    hdus = [M_hdu,LP_hdu,L_hdu,CS0_hdu,CS2_hdu,S_hdu]
    
    #concatenate the HDUs into an HDUList and write to fits file
    hdulist = fits.HDUList(hdus)
    hdulist.writeto(str(matrices_file_name),overwrite=True)

def file_exists(file_name):
    '''check to see if the fits file exists in the given address'''
    
    return os.path.isfile(str(file_name))

def save_kernel(kernel_file_name, kernel, key='T',overwrite=False):
    '''saves the kernel chosen by 'key' to the fits file
        initializes the fits file if it doesn't already exist'''
    
    
    #check to see if the file exists
    file_exists = os.path.isfile(str(kernel_file_name))
    if (not file_exists or overwrite==True):
        #initialize the fits file if it doesn't already exist
        warnings.warn("initializing fits file for the kernel...")
        init_kernel_fits(kernel_file_name)
    
    #open the file in update mode and write the kernel in the appropriate HDU, then close it
    kernel_hdul = fits.open(str(kernel_file_name),mode='update')
    kernel_hdul[key].data = kernel
    kernel_hdul.close()

def save_matrices(matrices_file_name, matrix, key='M',overwrite=False):
    '''saves the matrix chosen by 'key' to the fits file
    initializes the fits file if it doesn't already exist'''
    
    
    #check to see if the file exists
    file_exists = os.path.isfile(str(matrices_file_name))
    if (not file_exists or overwrite==True):
        #initialize the fits file if it doesn't already exist
        warnings.warn("initializing fits file...")
        init_matrices_fits(matrices_file_name)
    
    #open the file in update mode and write the matrix in the appropriate HDU, then close it
    kernel_hdul = fits.open(str(matrices_file_name),mode='update')
    kernel_hdul[key].data = matrix
    kernel_hdul.close()


def load_kernel(kernel_file_name, key='T'):
    '''loads the matrix chosen by 'key' from fits file'''
    
    
    # if the file exists, open it and read the HDU chosen by 'key'
    try:
        kernel_hdul = fits.open(str(kernel_file_name),mode='readonly')
        matrix = kernel_hdul[key].data
        kernel_hdul.close()

        return matrix

    #raise error if the file does not exist
    except IOError:
        print str(file_name)+" does not exist."

def load_matrix(matrices_file_name, key='M'):
    '''loads the matrix chosen by 'key' from fits file'''
    
    
    
    # if the file exists, open it and read the HDU chosen by 'key'
    try:
        kernel_hdul = fits.open(str(matrices_file_name),mode='readonly')
        matrix = kernel_hdul[key].data
        kernel_hdul.close()
        
        return matrix
    
    #raise error if the file does not exist
    except IOError:
        print str(file_name)+" does not exist."




