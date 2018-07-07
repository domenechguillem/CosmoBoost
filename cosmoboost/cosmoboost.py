
# coding: utf-8

# In[1]:

import sys
import os
import numpy as np 
np.set_printoptions(precision=7) 


# In[2]:

COSMOBOOST_DIR = os.path.dirname(os.path.realpath(__file__)) #os.getcwd()

sys.path.insert(0,COSMOBOOST_DIR)

import FileHandler as fh
import FrequencyFunctions as ff
import MatrixHandler as mh
import KernelODE 
import KernelRecursive as kr




DEFAULT_PARS = {
    'd' : 1,
    's' : 0,
    'beta' : -0.00123,
    'lmin' : 0,
    'lmax' : 1000,
    'delta_ell' : 3,
    'T_0':2.72548 ,#Kelvins
    'beta_exp_order':4, 
    'derivative_dnu':1.0,
    'normalize': True
}


# In[3]:

class Kernel(object):
    
    
    
    def __init__(self, pars=DEFAULT_PARS,
                 overwrite=False,save_kernel=True):
        
        # self._pars = pars
        
        self.d = pars['d']
        
        self.s = pars['s']
        self.beta = pars['beta']
        self.gamma = 1.0/np.sqrt(1-self.beta**2)
        self.lmin = pars['lmin']
        self.lmax = pars['lmax'] #+pars['delta_ell']
        self.T_0 = pars['T_0']
        self.derivative_dnu = pars['derivative_dnu']
        self.normalize = pars['normalize']
        #self._lmax_safe = pars['lmax']
        self.delta_ell = pars['delta_ell']
        self.beta_exp_order = pars['beta_exp_order']
        
        self.overwrite= overwrite
        self.save_kernel=save_kernel

        
        self.freq_func = ff.F_nu
        
        self.update()
        
    def update(self):
        
        self.pars = {
            'd' : self.d,
            's' : self.s,
            'beta' : self.beta,
            'lmin' : self.lmin,
            'lmax' : self.lmax,
            'delta_ell' : self.delta_ell,
            'T_0':self.T_0 ,#Kelvins
            'beta_exp_order':self.beta_exp_order,
            'derivative_dnu':self.derivative_dnu,
            'normalize': self.normalize
        }
        self.gamma = 1.0/np.sqrt(1-self.beta**2)
        
        self.kernel_filename = fh.kernel_filename(self.pars)
        self.matrices_filename = fh.matrices_filename(self.pars)
        
        
        self._init_matrices()
        self._init_mlpl()
        
        
        self.mlpl =[]

    def _init_matrices(self):
        if fh.file_exists(self.matrices_filename) and self.overwrite==False:
            print "matrices loaded from file: "+ self.matrices_filename
            self._load_matrices()
        else:
        
            print "Calculating the index matrices..."
            self.Mmatrix, self.Lmatrix = mh.ML_matrix(self.delta_ell,self.lmax)
            _,Clms = mh.Blm_Clm(delta_ell=self.delta_ell, lmax=self.lmax,s=self.s)
            self.Cmatrix = Clms[self.Lmatrix,self.Mmatrix]
            self.Smatrix = mh.S_matrix(self.Lmatrix,self.Mmatrix,self.s)
        
            #save Mmatrix and Lmatrix for future use
            #matrices_file_name = fh.matrices_filename(pars)
            dir_name = fh.dirname(lmax=self.lmax,beta=self.beta)
            if not os.path.exists(dir_name):
                os.makedirs(dir_name)
                fh.save_matrices(self.matrices_filename,self.Mmatrix,'M')
                fh.save_matrices(self.matrices_filename,self.Lmatrix,'L')
                print "Matrices saved in: " + self.matrices_filename

        
                print "Done!"
    
    def _init_mlpl(self):
    
        #initialize kernel with d=1    
        self._mlpl_d1 = self._get_mlpl_d1()
        #initialize (call setter) the mlpl coefficients for d=1
        self._mlpl  = self._mlpl_d1 
        #self._mlpl = self.mlpl
        self._lpl    = self._get_lpl()
    def _load_matrices(self):
        
        print "loading the index matrices..."
        self.Mmatrix = fh.load_matrix(self.matrices_filename,key="M")
        self.Lmatrix = fh.load_matrix(self.matrices_filename,key="L")
        #self.Lpmatrix = fh.load_matrix(self.matrices_filename,key="Lp")
        _,Clms = mh.Blm_Clm(delta_ell=self.delta_ell, lmax=self.lmax,s=self.s)
        self.Cmatrix = Clms[self.Lmatrix,self.Mmatrix]
        self.Smatrix = mh.S_matrix(self.Lmatrix,self.Mmatrix,self.s)
        print "Done!"
        


    
    
    @property #mlpl getter
    def mlpl(self):
        
        #print "get values for mlpl"
        return self._mlpl
        
            
    @mlpl.setter #mlpl setter
    def mlpl(self, value):
        if self.d == 1:
            #print "set d=1 values for mlpl"
            self._mlpl = self._mlpl_d1
        else:
            #print "set d>1 values for mlpl"
            self._mlpl = self._get_mlpl()

            
    @property #mlpl getter
    def lpl(self):
        
        #print "get values for mlpl"
        return self._get_lpl()
        
            
    @lpl.setter #mlpl setter
    def lpl(self, value):
        if self.d == 1:
            #print "set d=1 values for mlpl"
            self._lpl = self._get_lpl()
        else:
            #print "set d>1 values for mlpl"
            self._lpl = self._get_lpl()
#    @property #pars getter
#    def pars(self):
        
#        print "get values for mlpl"
#        return self._pars
    
    
#    @pars.setter #mlpl setter
#    def pars(self, value):



    def _get_mlpl_d1(self):
        '''return the DC aberration kernel elements K^m_{\ell' \ell} for d=1
        if the kernel has been calculated before, it will be loaded
        otherwise it will be calculated using the ODE'''
        
        #directory for saving/loading the aberration kernel elements 
        
        
        #load the aberration kernel if it exists,
        #otherwise calculate it by solving the kernel_ODE
        if fh.file_exists(self.kernel_filename) and self.overwrite==False:
            print "Kernel loaded from file: "+ self.kernel_filename
            K_mlpl = fh.load_kernel(self.kernel_filename,key='D1')
        else: 
            print "solving kernel ODE for d=1"
            K_mlpl = KernelODE.solve_K_T_ODE(self.pars,save_kernel=self.save_kernel)
        
        
        return K_mlpl
        
    def _get_mlpl(self):
        '''return the DC aberration kernel elements K^m_{\ell' \ell} for d!=1
        if the kernel has been calculated before, it will be loaded
        otherwise it will be calculated using the ODE'''
        if fh.file_exists(self.kernel_filename) and self.overwrite==False:
            print "Kernel loaded from file: "+ self.kernel_filename
        else:
            print "solving kernel ODE for d=1"
            self._get_mlpl_d1()
        
        return kr.K_d(self,self.d,self.s)
    
    def nu_mlpl(self,nu):
        
        K_d_arr = kr.get_K_d_arr(self,self.d,self.s)
        if self.pars['normalize']==True:
            return kr.K_nu_d_norm(K_d_arr,nu,self.pars,freq_func=self.freq_func)
        else:
            return kr.K_nu_d(K_d_arr,nu,self.pars,freq_func=self.freq_func)
        
        
    def d_arrary(self):
        return kr.get_K_d_arr(self,self.d)
    
    
        
    def _get_lpl(self):
        '''returns the Boost Power Transfer Matrix (BPTM) K_{lp,l} defined in ?'''
        K_mlpl = self.mlpl
        K_lpl = np.zeros((self.lmax+1,2*self.delta_ell+1))
        
        for lp in xrange(self.lmax+1):
            M = np.arange(self.lmin,lp+1)
        #K_delta[lp]=2*np.sum(K_mlp[fh.linenumb_mlp_vec(M,lp,lmax=lmax)])-K_mlp[fh.linenumb_mlp_vec(0,lp,lmax=lmax)]
            K_lpl[lp,:]=2*np.sum(K_mlpl[mh.mlp2indx(M,lp,self.lmax),:]**2,axis=0)-K_mlpl[mh.mlp2indx(0,lp,self.lmax),:]**2
            K_lpl[lp,:] /= 2*lp+1
        return K_lpl



        
def deboost_alm(alm,kernel,*nu):
    ''' deboost alm with the shape (n,(lmax+1)*(lmax+2)/2)
    where n = 1 for T only
    and   n = 3 for (T,E,B)
    if frequency nu is provided, the generalized aberation kernel coefficients will be used'''
    
    #if not isinstance(kernel,Kernel):
        #raise TypeError("the abberation kernel used is not an instance of the Kernel() class.") 
    
    #if len(alm.shape[1])!=kernel.mlpl.shape[0]:
    #    raise ValueError("the shape of alm vector and the kernel matrix doesn't match")
    
    if (np.ndim(alm)!=1 & (alm.shape[0]) not in (1,3)):
        raise ValueError("alm should be either 1 dimensional (T) or 3 dimentional (T, E, B)")
    
    
    #slice the temperature alm
    almT = alm[0]
    
    #initialize the boosted_alm array (1 or 3 dimensional)
    boosted_alm = np.zeros(alm.shape,dtype=np.complex)
    
    #set the first column to boosted almT
    boosted_alm[0] = _deboost_almT(almT,kernel)
    
    #return boosted T if alm is 1 dim
    if alm.shape[0] == 1:
        return boosted_alm[0]
    
    #return boosted E and B as well, if alm is 3 dim
    if alm.shape[0] == 3:
    
        almE = alm[1]
        almB = alm[2]
        
        boosted_almE = np.zeros(almE.shape)
        boosted_almB = np.zeros(almB.shape)
        
        
        boosted_alm[1:3] = _deboost_almEB(almE,almB,kernel)
        
    

    return boosted_alm




def _deboost_almT(almT,kernel):
    '''deboost temperature multipoles almT (s=0)'''
    

    print "deboosting almT\n"
    #if (almT.shape[0]!=1) : raise ValueError('almT.shape!=1')
    if (kernel.s !=0):
        kernel.s=0
        kernel.update()
    
    #delta_ell=kernel.delta_ell
    lmax=kernel.lmax
    
    #extention = (kernel.delta_ell*(2*kernel.lmax+1)+kernel.delta_ell**2)/2
    extention = kernel.delta_ell
    #extend the alm
    almT = np.append(almT,np.zeros(extention))
    
    Mmatrix = kernel.Mmatrix
    Lmatrix = kernel.Lmatrix
    
    print almT.shape
    print almT[mh.mlp2indx(Mmatrix,Lmatrix,lmax)].shape
    
    alm_boosted = np.sum(kernel.mlpl*almT[mh.mlp2indx(Mmatrix,Lmatrix,lmax)],axis=1 )    
    
    return alm_boosted


def _deboost_almEB(almE,almB,kernel):
    '''deboost polarization multipoles almE and almB (s=2)'''

    print "deboosting almEB\n"
    #if (almE.shape[0]!=1) : raise ValueError('almT.shape!=1')
    if (kernel.s !=2):
        kernel.s=2
        kernel.update()
    
    kernel_plus = kernel.mlpl
    
    kernel.s = -2
    kernel.update()
    
    kernel_minus= kernel.mlpl
    
    kernelEE_mlpl = 0.5 *(kernel_plus + kernel_minus)
    kernelEB_mlpl = 0.5j*(kernel_plus - kernel_minus)
    
    #delta_ell=kernel.delta_ell
    lmax=kernel.lmax
    
    #extention = (kernel.delta_ell*(2*kernel.lmax+1)+kernel.delta_ell**2)/2
    extention = kernel.delta_ell
    #extend the alm
    almE = np.append(almE,np.zeros(extention))
    almB = np.append(almB,np.zeros(extention))
    
    
    
    Mmatrix = kernel.Mmatrix
    Lmatrix = kernel.Lmatrix
    
    #sort and prepare alms for direct multiplication with kernel.mlpl
    alm_indx = mh.mlp2indx(Mmatrix,Lmatrix,lmax)
    
    almE_boosted = np.sum(kernelEE_mlpl*almE[alm_indx],axis=1 ) + np.sum(kernelEB_mlpl*almB[alm_indx],axis=1 )    
    almB_boosted = np.sum(kernelEE_mlpl*almB[alm_indx],axis=1 ) - np.sum(kernelEB_mlpl*almE[alm_indx],axis=1 )
    
    
    return np.vstack((almE_boosted,almB_boosted))


def boost_Cl(Cl,kernel):
    lmax = kernel.lmax
    delta_ell = kernel.delta_ell
    extention = (delta_ell*(2*lmax+1)+delta_ell**2)/2
    
    Cl_ext = np.append(Cl,np.zeros(extention))
    
    Lp = np.arange(lmax+1,dtype=int)
    L = np.tensordot(Lp,np.ones(2*delta_ell+1,dtype=int),axes=0) + np.arange(-delta_ell,delta_ell+1,dtype=int)
    
    Cl_boosted = np.sum(kernel.lpl()*Cl[L],axis=1)
    
    return Cl_boosted

