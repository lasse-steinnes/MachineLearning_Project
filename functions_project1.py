import numpy as np 
import matplotlib.pyplot as plt 
import subprocess
from sklearn.model_selection import train_test_split


from additional_functions_project1 import *

def matDesign (dataSet,order,indVariables):
    '''This is a function to set up the design matrix
    the inputs are :dataSet, the n datapoints, x and y data in a nx2 matrix
                    order, is the order of the coefficients, 
                    indVariables, the number of independant variables
                    
    i.e if order = 3 and indVariables = 1, then the number of coefficients THIS function will create is 4. (1 x x**2 x**3)
    or  if order = 2 and indVariables = 2, then the number of coefficients THIS function will create is 6. (1 x y xy x**2 y**2) 
    
    IMPORTANT NOTE: this works only for indVariables = 2 at the moment
    
    the outputs are X
    '''

    # if statement for the case with one independant variable
    if indVariables == 1:
        num_coeff = int(order + 1)
        
        # set up the Design matrix
        #n = np.int(np.size(dataSet))
        #matX = np.zeros((n,coefficients))
        
        n = np.shape(dataSet)[0]
        # loop through all the other columns as powes of dataSet
        
        matX = np.zeros((n,num_coeff))
        i = 0 #counter
        while i < num_coeff:

            matX[:,i] = (dataSet[i])**i
            i=i+1
        
        
    ###########################################################################################################
    
    # if statement for the case with two independant variables
    
    if (indVariables == 2):
        # find the number of coefficients we will end up with
        num_coeff = int((order + 1)*(order + 2)/2)
        #print ('The number of coefficients are: ',num_coeff)
                
        #find the number of rows in dataSet
        n = np.shape(dataSet)[0]
        #print ('The number of rows in the design matrix is', n)
        # create an empty matrix of zeros
        matX = np.zeros((n,num_coeff))
        

        
        col_G = 0 # global columns        
        tot_rows = n
        #print ('total rows = ',tot_rows)
        
        j = 0        
        # loop through each j e.g 1,2,3,4,5,6
        while j < num_coeff:
            k = 0
            #loop through each row
            while k <= j:                   
                row = 0                
                #loop through each item (each column in the row)
                while row < tot_rows:
                    matX[row,col_G] = ((dataSet[row,0])**(j-k)) * ((dataSet[row,1])**k)                                        
                    row = row + 1 
                    #print(row)
                    
                k = k + 1                     
            col_G = col_G + 1            
            j = j + 1

    
    return matX 



def linReg(data, design):
    """
    returns the estimated parameters of an OLS
    outputs variance as the diagonal entries of (X^TX)^-1
    """
    inverse = np.linalg.inv(design.T.dot(design))
    var = np.diag(inverse)
    par = inverse.dot(design.T).dot(data)
    return par, var

def ridgeReg(data, design, lam = 0.1):
    """
    returns the estimated parameters of an Ridge Regression with 
    regularization parameter lambda
    outputs variance as the diagonal entries of (X^TX- lam I)^-1
    """
    #creating identity matrix weighted with lam
    diag = lam * np.ones(design.shape[1])
    inverse = np.linalg.inv(design.T.dot(design) + np.diag(diag))
    var = diag(inverse)
    par = inverse.dot(design.T).dot(data)
    return par, var

def evaluate_model(data, design, par, par_var, regtype, lam =0, filepath ='', split = 0):
    """
    -calculates the MSE
    -calcualtes the variance and bias of the modell
    -outputs model information and saves it to filepath
    """
    p = par.shape[0]

    model = design.dot(par)
    expect_model = np.mean(model)

    mse = MSE(data, model)
    bias = MSE( data, expect_model)
    variance = MSE(model, expect_model)
    r2 = R2(data, model)
    
    #write to file
    try:
        f = open(filepath + "/"+ regtype+".txt",'w+')
    except:
        subprocess.call(["mkdir", filepath ])
        f = open(filepath +"pol_order"+str(p)+ "/"+ regtype+".txt",'w+')
    f.write("    Perfomance of %s regression with order %i \n:" %(regtype, p))
    if regtype != 'OLS':
        f.write("Regularization parameter lambda = %.4f\n" %lam)
    if split != 0:
        f.write("Validation on %.2f fraction of data set \n"%split)
    f.write("MSE = %.4f \t R2 = %.4f \t Bias(model)=%.4f \t Variance(model) =%.4f \n" %(mse, r2, bias, variance))
    f.write("Parameter Information:\n")
    for i in range(p):
        f.write("beta_%i=%.4f +- %.4f\n" %(i, par[i],np.sqrt(par_var[i])))
    f.close()
    return mse, r2, bias, variance

def run_fit_split(data, design, regtype, lam = 0.1, test_size= 1./3., filepath = ''):
    """
    perfomes the fit of the data to the model given as design matrix
    but first splitting it into a test and training set with fraction of data points
    going to the test set given by test_size
    suportet regtypes are 'OLS', 'RIDGE'
    lam is ignored for OLS
    returns a dictonary with all necessary information
    """
    design_train, design_test, data_train, data_test = train_test_split(design, data, test_size = test_size)
    if regtype == 'OLS':
        par, var = linReg(data_train, design_train)
    if regtype == 'RIDGE':
        par, var = ridgeReg(data_train, design_train, lam)

    mse, r2, bias, variance = evaluate_model(data_test, design_test, par, var,
                                                 regtype, lam, filepath, split= test_size )
    f = {'par' : par, 'par_var' : var, 'MSE': mse, 'R2' : r2, 
         'Model_Bias' : bias, 'Model_Variance' : variance, 'lambda' : lam }
    return f

    def run_fit(data, design, regtype, lam = 0.1, filepath = ''):
    """
    perfomes the fit of the data to the model given as design matrix
    suportet regtypes are 'OLS', 'RIDGE'
    lam is ignored for OLS
    returns a dictonary with all necessary information
    """
    if regtype == 'OLS':
        par, var = linReg(data, design)
    if regtype == 'RIDGE':
        par, var = ridgeReg(data, design, lam)

    mse, r2, bias, variance = evaluate_model(data, design, par, var,
                                                 regtype, lam, filepath )
    f = {'par' : par, 'par_var' : var, 'MSE': mse, 'R2' : r2, 
         'Model_Bias' : bias, 'Model_Variance' : variance, 'lambda' : lam }
    return f

