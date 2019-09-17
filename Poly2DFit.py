from additional_functions_project1 import MSE, R2, FrankeFunction, plot_it
import numpy as np
import subprocess
import warnings
from sklearn.model_selection import train_test_split
from sklearn.linear_model import Lasso


class Poly2DFit:
    """
    class which perfoms a 2D polynomial fit to given data or generated samples from the Franke function
    Class Variables:
     -dependentvariables are stored in x,y and the constructed design matrix in _design
     -data to fit in data
     -order of the polynomial to use in order
     -all perfomrance information are stored in mse, r2, variance, bias
     - parameters and theri variance are stored in par, par_var
    Class Methodes:
        -generateSample from Franke function
        -givenData input real data
        -matDesign creates a design matrix
        -_linReg and _ridgeReg calculate parameters with respectivly regression type and calculate parameter variance
        - runFit performes the fit
    """
    def __init__(self):
        """
        initialize kfold flag
        """
        self.kfold = False
        #set seed for comparability
        np.random.seed(159)
        self.mse = 0
        self.mse_train = 0
        self.r2 = 0
        self.variance = 0
        self. bias = 0


    def generateSample(self, n, mean = 0., var = 1):
        """
        This function creates a sample [x,y,z] where x,y are uniform random numbers [0,1)
        and z = f(x,y) + eps with f the Franke function and eps normal distributed with mean and var

        """

        #use same random numbers each time to make evaulating easier
        #create x and y randomly
        self.x, self.y = np.random.rand(2,n)

        #pass the x and y data into the Franke function this will be used later in evaluating the model
        self.data = FrankeFunction(self.x, self.y) + np.sqrt(var)*np.random.randn(n) + mean

    def givenData(self, x, y, f):
        """
        stores given 2D data in class
        x,y are dependent variables, f= f(x,y)
        """
        self.x = x
        self.y = y
        self.data = f


    def kfold_cross(self, Pol_order, regtype, lam = 0.1, k= 1):
        """
        runs the k-Fold cross-validation on the given data
        sets the training example afterwards to self.x, self.y, self.data
        sets kfold flag to True
        """
        self.k = k
        self.kfold = True
        kinv = 1.0/k
        #determin length

        np.random.seed(0)
        np.random.shuffle(self.x)
        np.random.seed(0)
        np.random.shuffle(self.y)
        np.random.seed(0)
        np.random.shuffle(self.data)
   
        x_folds = np.array_split(self.x, k)
        y_folds = np.array_split(self.y, k)
        data_folds = np.array_split(self.data, k)
        
        #allow simple splitting in test and training data
        if k ==  1 :
            self.xtrain, self.xtest, self.ytrain, self.ytest, self.datatrain, self.datatest = train_test_split(self.x, self.y, self.data, shuffle = True, test_size = 4/5)
            Poly2DFit.run_fit(self, Pol_order, regtype, lam)
            self.mse_train += Poly2DFit.evaluate_model(self, self.k)
        else:
            for i in range(k):
                xtrain = np.delete(x_folds, i , 0)
                ytrain = np.delete(x_folds, i , 0)
                datatrain = np.delete(data_folds, i , 0)

                self.xtrain = np.concatenate(xtrain)
                self.xtest  = x_folds[i]
                self.ytrain = np.concatenate(ytrain)
                self.ytest  = y_folds[i]
                self.datatrain = np.concatenate(datatrain)
                self.datatest  = data_folds[i]


                Poly2DFit.run_fit(self, Pol_order, regtype, lam)
                self.mse_train += Poly2DFit.evaluate_model(self, self.k)


    def run_fit(self, Pol_order, regtype, lam = 0.1):
        """
        perfomes the fit of the data to the model given as design matrix
        suportet regtypes are 'OLS', 'RIDGE'
        lam is ignored for OLS
        returns fit parameters and their variance
        """
        self.order = Pol_order
        self.lam = lam
        self.regType = regtype
        self.model = np.zeros(self.data.shape)

        if self.kfold:
            Poly2DFit.matDesign(self, self.xtrain, self.ytrain)
        else:
            Poly2DFit.matDesign(self, self.x, self.y)

        if regtype == 'OLS':
            Poly2DFit._linReg(self)
        if regtype == 'RIDGE':
            Poly2DFit._ridgeReg(self)
        if regtype == 'LASSO':
            Poly2DFit._lasso(self)

        return self.par, self.par_var

    def _linReg(self):
        """
        calculates the estimated parameters of an OLS
        outputs variance as the diagonal entries of (X^TX)^-1
        """
        XTX = self._design.T.dot(self._design)
        #try to use standard inversion, otherwise use SVD
        try:
            inverse = np.linalg.inv(XTX)
        except:
            print("in exception")
            raise warnings.warn("Singular Matrix: Using SVD", Warning)
            U, S, VT = np.linalg.svd(XTX)
            inverse = VT.T.dot(np.diag(1/S)).dot(U.T)

        self.par_var = np.diag(inverse)
        if self.kfold:
            self.par = inverse.dot(self._design.T).dot(self.datatrain)
        else:
            self.par = inverse.dot(self._design.T).dot(self.data)

    def _ridgeReg(self):
        """
        returns the estimated parameters of an Ridge Regression with
        regularization parameter lambda
        outputs variance as the diagonal entries of (X^TX- lam I)^-1
        """
        #creating identity matrix weighted with lam
        diag = self.lam * np.ones(self._design.shape[1])
        XTX_lam = self._design.T.dot(self._design) + np.diag(diag)
        #try to use standard inversion, otherwise use SVD
        try:
            inverse = np.linalg.inv(XTX_lam)
        except:
            warnings.warn("Singular Matrix: Using SVD", Warning)
            U, S, VT = np.linalg.svd(XTX_lam)
            inverse = VT.T.dot(np.diag(1/S)).dot(U.T)

        self.par_var = np.diag(inverse)

        if self.kfold:
            self.par = inverse.dot(self._design.T).dot(self.datatrain)
        else:
            self.par = inverse.dot(self._design.T).dot(self.data)

    def _lasso(self):
        """
        Creates a model using Lasso, Returns the estimated output z
        """
        lasso = Lasso(alpha=self.lam, max_iter=10e7)
        # creates the Lasso parameters, beta
        if self.kfold:
            clf =  lasso.fit(self._design,self.datatrain)
            self.par = clf.coef_
        else:
            clf =  lasso.fit(self._design,self.data)
            self.par = clf.coef_
        self.par_var = 0

    def matDesign (self, x , y , indVariables = 2):
        '''This is a function to set up the design matrix
        the inputs are :dataSet, the n datapoints, x and y data in a nx2 matrix
                        order, is the order of the coefficients,
                        indVariables, the number of independant variables

        i.e if order = 3 and indVariables = 1, then the number of coefficients THIS function will create is 4. (1 x x**2 x**3)
        or  if order = 2 and indVariables = 2, then the number of coefficients THIS function will create is 6. (1 x y xy x**2 y**2)

        IMPORTANT NOTE: this works only for indVariables = 1, 2 at the moment
        the outputs are X
        '''
        #stack data
        dataSet = np.vstack((x, y)).T

        # if statement for the case with one independant variable
        if indVariables == 1:
            num_coeff = int(self.order + 1)

            # set up the Design matrix
            #n = np.int(np.size(dataSet))
            #matX = np.zeros((n,coefficients))

            n = np.shape(dataSet)[0]
            # loop through all the other columns as powes of dataSet

            self._design = np.zeros((n,num_coeff))
            i = 0 #counter
            while i < num_coeff:

                self._design[:,i] = (dataSet[i])**i
                i=i+1


        ###########################################################################################################

        # if statement for the case with two independant variables

        if (indVariables == 2):
            # find the number of coefficients we will end up with
            num_coeff = int((self.order + 1)*(self.order + 2)/2)
            #print ('The number of coefficients are: ',num_coeff)

            #find the number of rows in dataSet
            n = np.shape(dataSet)[0]
            #print ('The number of rows in the design matrix is', n)
            # create an empty matrix of zeros
            self._design = np.zeros((n,num_coeff))



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
                        self._design[row,col_G] = ((dataSet[row,0])**(j-k)) * ((dataSet[row,1])**k)
                        row = row + 1
                        #print(row)


                    k = k + 1
                col_G = col_G + 1
                j = j + 1

    def evaluate_model(self, k = 1):

        """
        -calculates the MSE
        -calcualtes the variance and bias of the modell
        returns the modelpoints
        """
        p = self.par.shape[0]


        if self.kfold:
            #model with training input
            model_train = self._design.dot(self.par)
            MSE_train = MSE(self.datatrain, model_train)

            Poly2DFit.matDesign(self, self.xtest, self.ytest)
            #model with training and test input
            model_test = self._design.dot(self.par)

            expect_model = np.mean(model_test)

            self.mse += MSE(self.datatest, model_test)/self.k
            self.r2 += R2(self.datatest, model_test)/self.k


            #self.bias = MSE(FrankeFunction(self.xtest, self.ytest), expect_model) # explain this in text why we use FrankeFunction
            self.variance += MSE(model_test, expect_model)/self.k
            #alternative implementaton
            # MSE = bias + variance + data_var <-> bias = MSE - varinace - data_var
            #what is data var?

            self.bias += (self.mse - self.variance - np.var([self.x, self.y]))/self.k
            self.model += np.append(model_train, model_test)/self.k
            
            #returning the  weighted MSE on training data
            return MSE_train/self.k

        else:

            self.model = self._design.dot(self.par)

            expect_model = np.mean(self.model)

            self.mse = MSE(self.data, self.model)
            self.r2 = R2(self.data, self.model)


            #self.bias = MSE(FrankeFunction(self.x, self.y), expect_model) # explain this in text why we use FrankeFunction
            self.variance = MSE(self.model, expect_model)
            self.bias = self.mse - self.variance - np.var([self.x, self.y])



    def plot_function(self):
        """
        This functions:
        -plots the x,y and franke function data in a scatter plot
        -plots the x,y and model in a triangulation plot
        """
        self.plot_function = plot_it(self.x, self.y, self.model, self.data)


    def store_information(self, filepath, filename):

        try:
            f = open(filepath + "/" + filename  + ".txt",'w+')
        except:
            subprocess.call(["mkdir", "-p", filepath ])
            f = open(filepath + "/"+ filename + ".txt",'w+')

        f.write("    Perfomance of %s regression with  %i parameters \n:" %(self.regType, len(self.par)))

        if self.regType != 'OLS':
            f.write("Regularization parameter lambda = %f\n" %self.lam)

        if self.kfold:
            f.write("k-fold cross-validation with %i runs \n" %self.k)

        f.write("MSE = %.4f \t R2 = %.4f \t Bias(model)=%.4f \t Variance(model) =%.4f \n" %(self.mse, self.r2, self.bias, self.variance))
        f.write("Parameter Information:\n")
        for i in range(len(self.par)):
            f.write("beta_%i = %.4f +- %.4f\n" %(i, self.par[i], np.sqrt(self.par_var[i])) )
        f.close()
