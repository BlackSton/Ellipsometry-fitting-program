# -*- coding: utf-8 -*-
"""
Created on Sun Aug  8 20:29:55 2021

@author: rltjr
"""
from scipy import optimize
from scipy.stats import chisquare
import numpy as np


class Function():
    def __init__(self):
        self.eV_O = np.linspace(6.2,0,1000) # eV Original Data
        self.Sigma_O = np.linspace(3000,3000,1000) # Sigma Original Data
        self.eV = np.linspace(6.2,0,1000) # eV Fitting Data
        self.Sigma = np.linspace(3000,3000,1000) # Sigma Fitting Data
        self.c = 8065.5
        self.RT = 300e-6
        self.RT_State = False
        self.FuncI =[]
        self.Init = []
        self.Low_Boundary = []
        self.High_Boundary = []
        # self.Init =[1,1,0,
        #                 0.1,0.1,1,
        #                 2,0.1,3,
        #                 0.1,0.1,4.4,
        #                 0.1,0.1,5.6]
        # self.Low_Boundary  =[0.0,0.0,0.0,
        #                      0.0,0.0,0.0,
        #                      0.0,0.0,0.0,
        #                      0.0,0.0,0.0,
        #                      0.0,0.0,0.0]
        # self.High_Boundary =[50,10,10,
        #                      10 ,10, 10,
        #                      10 ,10, 10,
        #                      10 ,10, 10,
        #                      10 ,10, 10]
        self.Residual = 'X'
        self.LossFunction = 'soft_l1'
        self.res = 0
        self.Iterations = 100
    def roadsetting(self,data):
        self.FuncI = data[:,0]
        self.Low_Boundary  = np.concatenate((data[:,1],data[:,4],data[:,7]))
        self.Init          = np.concatenate((data[:,2],data[:,5],data[:,8]))
        self.High_Boundary = np.concatenate((data[:,3],data[:,6],data[:,9]))
    def Drude(self,A,Br,xc=0):    
        return (A*self.c*Br/60)/(self.eV**2+Br**2)
    def Drude_RT(self,A,Br=0,xc=0):
        Br = A*self.c*self.RT/60
        return (A*self.c*Br/60)/(self.eV**2+Br**2)
    def Lorentz(self,A,Br,xc):
        return (A*(xc**2)*Br*self.c*(self.eV**2)/60)/((xc**2-(self.eV)**2)**2+((Br**2)*(self.eV)**2))
    ###### PLOT #######
    def Drude_Plot(self,A,Br,xc=0,x=0):
        if self.RT_State == False:
            return (A*self.c*Br/60)/(x**2+Br**2)
        else:
            Br = A*self.c*self.RT/60
            return (A*self.c*Br/60)/(x**2+Br**2)
    def Lorentz_Plot(self,A,Br,xc,x):
        return (A*(xc**2)*Br*self.c*(x**2)/60)/((xc**2-(x)**2)**2+((Br**2)*(x)**2))
    def Plot(self,v,x):
        Sum = x * 0
        count = 0
        for Func_N in self.FuncI:
            if Func_N == 1: # if Func is Drude
                Sum = Sum + self.Drude_Plot(v[count],v[count+len(self.FuncI)],v[count+2*len(self.FuncI)],x)
            elif Func_N == 2:
                Sum = Sum + self.Lorentz_Plot(v[count],v[count+len(self.FuncI)],v[count+2*len(self.FuncI)],x)
            count = count + 1
        return Sum
    
    
    ###### PLOT #######
    def Func(self,v):
        Sum = self.Sigma * 0
        count = 0
        for Func_N in self.FuncI:
            if Func_N == 1: # if Func is Drude
                if self.RT_State == False:
                    Sum = Sum + self.Drude(v[count],v[count+len(self.FuncI)],v[count+2*len(self.FuncI)])
                else:
                    Sum = Sum + self.Drude_RT(v[count],v[count+len(self.FuncI)],v[count+2*len(self.FuncI)])
            elif Func_N == 2:
                Sum = Sum + self.Lorentz(v[count],v[count+len(self.FuncI)],v[count+2*len(self.FuncI)])
            count = count + 1
        return Sum
    def Rasidual_X(self,params):
        return np.abs(self.Sigma - self.Func(params))
    def Rasidual_X2(self,params):
        return np.square(self.Sigma - self.Func(params))
    def Rasidual_Log(self,params):
        return np.abs(np.log10(self.Sigma) - np.log10(self.Func(params)))
    def Rasidual_Log2(self,params):
        return np.square(np.log10(self.Sigma) - np.log10(self.Func(params)))
    def chi_square(self,params):
        fobs = np.array(self.Sigma)
        fexp = np.array(self.Func(params))
        #fexp = fexp * (np.sum(fobs)/np.sum(fexp)) 
        return chisquare(fobs,f_exp = fexp)[0]
    
    ##### Residual #####
    # * 'linear' (default) : ``rho(z) = z``. Gives a standard
    #           least-squares problem.
    # * 'soft_l1' : ``rho(z) = 2 * ((1 + z)**0.5 - 1)``. The smooth
    #   approximation of l1 (absolute value) loss. Usually a good
    #   choice for robust least squares.
    # * 'huber' : ``rho(z) = z if z <= 1 else 2*z**0.5 - 1``. Works
    #   similarly to 'soft_l1'.
    # * 'cauchy' : ``rho(z) = ln(1 + z)``. Severely weakens outliers
    #   influence, but may cause difficulties in optimization process.
    # * 'arctan' : ``rho(z) = arctan(z)``. Limits a maximum loss on
    #   a single residual, has properties similar to 'cauchy'.
    def F_linear(self,z):
        return z
    def F_soft_l1(self,z):
        return 2 * ((1 + z)**0.5 - 1)
    def F_huber(self,z):
        return z if z <= 1 else 2*z**0.5 - 1
    def F_cauchy(self,z):
        return np.ln(1 + z)
    def F_arctan(self,z):
        return np.arctan(z)
    
    ##### Fit line #####
    def Fit(self):
        if self.Residual == 'X':
            self.res = optimize.least_squares(self.Rasidual_X,self.Init,
                                              bounds=(self.Low_Boundary,self.High_Boundary),
                                              loss=self.LossFunction,method='trf',max_nfev = self.Iterations)
        elif self.Residual == 'X^2':
            self.res = optimize.least_squares(self.Rasidual_X2,self.Init,
                                              bounds=(self.Low_Boundary,self.High_Boundary),
                                              loss=self.LossFunction,method='trf',max_nfev = self.Iterations)
        elif self.Residual == 'Log':
            self.res = optimize.least_squares(self.Rasidual_Log,self.Init,
                                              bounds=(self.Low_Boundary,self.High_Boundary),
                                              loss=self.LossFunction,method='trf',max_nfev = self.Iterations)
        elif self.Residual == 'Log^2':
            self.res = optimize.least_squares(self.Rasidual_Log2,self.Init,
                                              bounds=(self.Low_Boundary,self.High_Boundary),
                                              loss=self.LossFunction,method='trf',max_nfev = self.Iterations)
        elif self.Residual == 'chi^2':
            bound = optimize.Bounds(self.Low_Boundary,self.High_Boundary)
            self.res  = optimize.minimize(fun=self.chi_square, x0=self.Init,
                                          bounds=bound, method = 'SLSQP',
                                          options={"ftol":1e-8,"maxiter":self.Iterations})
            self.res.cost = self.res.fun
        self.Init = self.res.x # Changing the initial value
    def Fit_NB(self):
        self.res = optimize.least_squares(self.Rasidual_Square,self.Init,loss=self.loss,method='trf')