from logistic_regression import LogisticRegression
import helpers
import numpy as np


class SAMME():
    '''
    Multi-class Adaboost (SAMME)
    Saharon Rossett, Trevor Hastie, Jia Zhu (2006)
    '''
    def __init__(self, n_classes, n_learners, X_train, Y_train):
        '''
        Initialize all parameters
        '''
        self.X_train = X_train
        self.Y_train = Y_train
        self.n_classes = n_classes
        self.n_learners = n_learners
        self.n_samples = max(self.X_train.shape)
        self.n_features = min(self.X_train.shape)


        # Initialize observation weights and learner weights appropriately
        self.w = np.full(self.n_samples, (1 / self.n_samples), dtype=np.float32)
        self.learner_weights = np.zeros((self.n_learners,), dtype=np.float32)
        self.learners = []


    def resample(self):
        '''
        We are implementing multi-class Adaboost with resampling
        as opposed to reweighting
        '''
        new_obs = np.random.choice(np.arange(self.n_samples), size=self.n_samples, p=self.w)

        print(np.unique(new_obs, return_counts=True))

        X_train_new = self.X_train[new_obs, :]
        Y_train_new = self.Y_train[new_obs]

        return(X_train_new, Y_train_new)


    def train(self):
        '''
        Training loop for SAMME
        '''
        
        # Initial training sets are just copies of the input sets
        X_train_new = np.copy(self.X_train)
        
        # Initial labels are just copies of the input sets
        Y_train_new = np.copy(self.Y_train)

        
        
        for learner_id in range(self.n_learners):

            learner = LogisticRegression(lr=0.01, epochs=1000, n_classes=self.n_classes, 
                                         n_features=self.n_features, X_train=X_train_new, Y_train=Y_train_new)

            # Train weak learner
            learner.train()
            
            # Get predictions
            preds, loss = learner.predict(self.X_train, self.Y_train)
            
            # Calculate mistakes
            mistakes = (preds != self.Y_train).astype(int)

            print(np.sum(mistakes)/len(Y_train))

            # Compute the weighted learner error
            weighted_learner_error = np.sum(mistakes * self.w)/np.sum(self.w)

            # Compute alpha if the learner is not qualified, set to 0
            self.learner_weights[learner_id] = max(0, np.log(1/(weighted_learner_error + 1e-6) - 1) + np.log(self.n_classes - 1))
            
            # Create alpha matrix that we can use to take an element-wise product with the mistakes vector
            alpha = np.full((self.n_samples,), fill_value=self.learner_weights[learner_id], dtype=np.float32)
            
            # Update entry weights, prediction made by unqualified learner will not update the entry weights
            self.w= self.w * np.exp(alpha * mistakes)
            
            # Normalize the entry weights
            self.w = self.w/np.sum(self.w)

            # Resample according to the updated weights
            X_train_new, Y_train_new = self.resample()

            self.learners.append(learner)

        self.learner_weights = self.learner_weights/np.sum(self.learner_weights)


    def predict(self, X, Y):
        """
        Predict using the boosted learner
        :param X:
        :return: predict class
        """
        pooled_prediction = np.zeros((self.n_classes, len(Y)), dtype=np.float32)

        for learner_id, learner in enumerate(self.learners):
            
            
            preds, _ = learner.predict(X, Y)

            preds = preds.astype(int)

            # Encode the prediction in to balanced array
            prediction = np.full((self.n_classes, len(Y)), fill_value=-1/(self.n_classes-1), dtype=np.float32)

            for obs, pred in enumerate(list(preds)):

              prediction[pred, obs] = 1

            prediction = prediction*self.learner_weights[learner_id]
            
            pooled_prediction += prediction

        pooled_predictions = np.argmax(pooled_prediction, axis = 0)

        loss = np.sum(pooled_predictions != Y)/len(Y)

        return pooled_predictions, loss



if __name__ == '__main__':

   np.random.seed(13290)

   data_args = {

        'data_path': '../data',
        'name': 'zipcombo.dat', 
        'train_percent': 0.8,
        'k': 5,

        }

   # Load full dataset
   X, Y = helpers.load_data(data_args['data_path'], data_args['name'])
    
   # Shuffle and split dataset
   X_shuffle, Y_shuffle, perm = helpers.shuffle_data(X,Y)
    
   # Split dataset
   X_train, X_val, Y_train, Y_val, _, _ = helpers.split_data(X_shuffle, Y_shuffle, perm, data_args['train_percent'])

   n_classes=10
   
   n_learners=2

   example_samme = SAMME(n_classes, n_learners, X_train, Y_train)

   example_samme.train()

   preds, loss = example_samme.predict(X_train, Y_train)

   preds, val_loss = example_samme.predict(X_val, Y_val)

   print(loss, val_loss)



