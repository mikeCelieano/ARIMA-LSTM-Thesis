import numpy as np

def calculate_comprehensive_metrics(actual_values, predictions_dict):
    """
    Menghitung MAE, MAPE, RMSE, dan CI Coverage untuk semua model.
    Format output disesuaikan agar mudah di-render oleh UI secara side-by-side.
    """
    results = {}
    
    # actual_values biasanya array/list dari proses backtesting
    # Untuk metrik real-world sederhana 1-step forecast, kita asumsikan 
    # data ini dipanggil dari loop backtesting di pipeline.
    
    for model_name, preds in predictions_dict.items():
        actual = np.array([p['actual'] for p in preds])
        predicted = np.array([p['predicted'] for p in preds])
        lower_ci = np.array([p['lower_ci'] for p in preds])
        upper_ci = np.array([p['upper_ci'] for p in preds])

        errors = actual - predicted
        
        mae = np.mean(np.abs(errors))
        mape = np.mean(np.abs(errors / actual)) * 100
        rmse = np.sqrt(np.mean(errors ** 2))
        
        # Menghitung persentase nilai aktual yang masuk dalam rentang CI
        within_ci = ((actual >= lower_ci) & (actual <= upper_ci))
        ci_coverage = np.mean(within_ci) * 100
        
        results[model_name] = {
            "MAE": mae,
            "MAPE": mape,
            "RMSE": rmse,
            "CI Coverage": ci_coverage
        }
        
    return results