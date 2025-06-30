import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.callbacks import EarlyStopping
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, mean_squared_error, r2_score, mean_absolute_error


class EarthquakeLSTMPredictor:
    def __init__(self, look_back=10):
        self.look_back = look_back
        self.model = None
        self.scaler_x = MinMaxScaler()
        self.scaler_y = MinMaxScaler()

    def prepare_data(self, data):
        features = ['x', 'y', 'z', 'magnitude']
        X = data[features].values
        y = data['status'].values

        X_scaled = self.scaler_x.fit_transform(X)
        y_scaled = self.scaler_y.fit_transform(y.reshape(-1, 1))

        X_sequences, y_sequences = [], []
        for i in range(len(X_scaled) - self.look_back):
            X_sequences.append(X_scaled[i:i + self.look_back])
            y_sequences.append(y_scaled[i + self.look_back])

        X_sequences = np.array(X_sequences)
        y_sequences = np.array(y_sequences)

        return train_test_split(X_sequences, y_sequences, test_size=0.2, random_state=42)

    def build_lstm_model(self, input_shape):
        model = Sequential([
            LSTM(64, activation='relu', input_shape=input_shape, return_sequences=True),
            Dropout(0.2),
            LSTM(32, activation='relu'),
            Dropout(0.2),
            Dense(16, activation='relu'),
            Dense(1, activation='sigmoid')
        ])
        model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
        return model

    def train(self, data):
        X_train, X_test, y_train, y_test = self.prepare_data(data)

        input_shape = (X_train.shape[1], X_train.shape[2])
        self.model = self.build_lstm_model(input_shape)

        early_stop = EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True)

        history = self.model.fit(
            X_train, y_train,
            epochs=100,
            validation_split=0.2,
            callbacks=[early_stop],
            verbose=1
        )

        # Save model
        self.model.save('earthquake_lstm_model.h5')

        # Evaluate on test data
        y_pred = (self.model.predict(X_test) > 0.5).astype(int)

        # Classification Metrics
        accuracy = accuracy_score(y_test, y_pred)
        precision = precision_score(y_test, y_pred)
        recall = recall_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred)

        # Regression Metrics
        mse = mean_squared_error(y_test, y_pred)
        rmse = np.sqrt(mse)
        mae = mean_absolute_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)

        # Print metrics
        print(f"\n✅ Model Accuracy: {accuracy * 100:.2f}%")
        print(f"✅ Precision: {precision:.4f}")
        print(f"✅ Recall: {recall:.4f}")
        print(f"✅ F1-Score: {f1:.4f}")
        print(f"✅ MSE: {mse:.6f}")
        print(f"✅ RMSE: {rmse:.6f}")
        print(f"✅ MAE: {mae:.6f}")
        print(f"✅ R² Score: {r2:.6f}")

        # Save performance plots
        self.plot_and_save_metrics(history, accuracy, precision, recall, f1, mse, rmse, r2)

    def plot_and_save_metrics(self, history, accuracy, precision, recall, f1, mse, rmse, r2):
        """Generate and save accuracy, precision, recall, F1-score, MSE, RMSE, and R² graphs"""

        plt.figure(figsize=(12, 6))

        # Accuracy & Loss Plot
        plt.subplot(2, 2, 1)
        plt.plot(history.history['accuracy'], label='Train Accuracy', color='blue')
        plt.plot(history.history['val_accuracy'], label='Validation Accuracy', color='cyan')
        plt.title('Model Accuracy')
        plt.xlabel('Epoch')
        plt.ylabel('Accuracy')
        plt.legend()
        plt.grid()

        plt.subplot(2, 2, 2)
        plt.plot(history.history['loss'], label='Train Loss', color='red')
        plt.plot(history.history['val_loss'], label='Validation Loss', color='orange')
        plt.title('Model Loss')
        plt.xlabel('Epoch')
        plt.ylabel('Loss')
        plt.legend()
        plt.grid()

        # Classification and Regression Metrics
        plt.subplot(2, 2, 3)
        metrics = ['Accuracy', 'Precision', 'Recall', 'F1-Score']
        values = [accuracy, precision, recall, f1]
        colors = ['blue', 'green', 'orange', 'red']

        bars = plt.bar(metrics, values, color=colors)
        plt.ylim(0, 1.5)  # Adjusted to fit MSE/RMSE if needed
        plt.title('Final Model Metrics')

        # Add values on top of bars
        for bar, value in zip(bars, values):
            plt.text(bar.get_x() + bar.get_width() / 2, bar.get_height(),
                     f'{value:.4f}', ha='center', va='bottom', fontsize=12, fontweight='bold')

        plt.tight_layout()
        plt.savefig('model_metrics.png')
        plt.close()

    def load_and_predict(self, input_data):
        # Load saved model
        loaded_model = load_model('earthquake_lstm_model.h5')

        # Prepare input data
        features = ['x', 'y', 'z', 'magnitude']
        input_sequence = input_data[features].values
        input_scaled = self.scaler_x.transform(input_sequence)
        input_reshaped = input_scaled.reshape(1, self.look_back, input_scaled.shape[1])

        # Predict
        prediction = loaded_model.predict(input_reshaped)[0][0]

        return {
            'earthquake_probability': prediction,
            'status': 1 if prediction > 0.5 else 0
        }


def main():
    # Load dataset
    data = pd.read_csv('earthquake.csv')

    # Initialize predictor
    predictor = EarthquakeLSTMPredictor()

    # Train and save model
    predictor.train(data)

    # Load model and predict on sample data
    sample_data = data.iloc[-10:]
    prediction = predictor.load_and_predict(sample_data)
    print("Earthquake Prediction:", prediction)


if __name__ == '__main__':
    main()