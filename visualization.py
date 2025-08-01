import matplotlib.pyplot as plt
import os
import numpy as np

def plot_stock_prediction(ticker, test_indices, actual_prices, predicted_prices, metrics, save_dir, model_type):
    """
    绘制股票预测结果对比图
    
    参数:
        ticker: 股票代码
        test_indices: 测试集日期索引
        actual_prices: 实际价格
        predicted_prices: 预测价格
        metrics: 包含rmse、mae和accuracy的字典
        save_dir: 图片保存的根目录
        model_type: 模型类型 ('LSTM' 或 'GRU')
    返回:
        str: 保存的图片路径
    """
    try:
        plt.figure(figsize=(15, 7))
        plt.plot(test_indices, actual_prices, label='Actual Price', color='blue', linewidth=2, alpha=0.7)
        plt.plot(test_indices, predicted_prices, label=f'{model_type} Prediction', color='red', linewidth=2, linestyle='--', alpha=0.7)
    
        plt.title(f'{ticker} Stock Price Prediction ({model_type})\nRMSE: {metrics["rmse"]:.2f}, MAE: {metrics["mae"]:.2f}')
        plt.xlabel('Date')
        plt.ylabel('Price')
        plt.xticks(rotation=45)
        plt.grid(True, alpha=0.3)
        plt.legend()
    
        plt.text(0.02, 0.95, f'Prediction Accuracy: {metrics["accuracy"]*100:.2f}%',
                 transform=plt.gca().transAxes, bbox=dict(facecolor='white', alpha=0.8))
    
        plt.tight_layout()
    
        prediction_dir = os.path.join(save_dir, 'pic/predictions')
        os.makedirs(prediction_dir, exist_ok=True)
        save_path = os.path.join(prediction_dir, f'{ticker}_{model_type}_prediction.png')
        plt.savefig(save_path)
        plt.close()
    
        return save_path
    except Exception as e:
        print(f"Error plotting stock prediction for {ticker}: {e}")
        plt.close()
        return None

def plot_training_loss(ticker, train_losses, val_losses, save_dir, model_type=None):
    """
    绘制训练和验证损失曲线
    
    参数:
        ticker: 股票代码
        train_losses: 训练损失列表
        val_losses: 验证损失列表
        save_dir: 图片保存的根目录
        model_type: 模型类型 ('LSTM' 或 'GRU')，可选
    返回:
        str: 保存的图片路径
    """
    try:
        plt.figure(figsize=(10, 5))
        plt.plot(train_losses, label='Train Loss')
        plt.plot(val_losses, label='Validation Loss')
        plt.xlabel('Epoch')
        plt.ylabel('Loss')
        title = f'Training and Validation Loss for {ticker}'
        if model_type:
            title += f' ({model_type})'
        plt.title(title)
        plt.legend()
        plt.grid(True)
    
        loss_dir = os.path.join(save_dir, 'pic/loss')
        os.makedirs(loss_dir, exist_ok=True)
        filename = f'{ticker}_loss.png'
        if model_type:
            filename = f'{ticker}_{model_type}_loss.png'
        save_path = os.path.join(loss_dir, filename)
        plt.savefig(save_path)
        plt.close()
    
        return save_path
    except Exception as e:
        print(f"Error plotting training loss for {ticker}: {e}")
        plt.close()
        return None

def plot_cumulative_earnings(ticker, test_indices, actual_percentages, predict_percentages, save_dir, model_type):
    """
    绘制累积收益率曲线
    
    参数:
        ticker: 股票代码
        test_indices: 测试集日期索引
        actual_percentages: 实际收益率列表
        predict_percentages: 预测收益率列表
        save_dir: 图片保存的根目录
        model_type: 模型类型 ('LSTM' 或 'GRU')
    返回:
        str: 保存的图片路径
    """
    try:
        cumulative_naive_percentage = np.cumsum(actual_percentages)
        cumulative_model_percentage = np.cumsum(
            [a if p > 0 else 0 for p, a in zip(predict_percentages, actual_percentages)]
        )

        plt.figure(figsize=(10, 6))
        plt.plot(test_indices, cumulative_naive_percentage, marker='o', markersize=3,
                 linestyle='-', color='blue', label='Naive Strategy')
        plt.plot(test_indices, cumulative_model_percentage, marker='o', markersize=3,
                 linestyle='-', color='orange', label=f'{model_type} Strategy')
        plt.title(f'Cumulative Earnings Percentages for {ticker} ({model_type})')
        plt.xlabel('Date')
        plt.ylabel('Percentage (%)')
        plt.xticks(rotation=45)
        plt.grid(True)
        plt.legend()
        plt.tight_layout()
    
        earnings_dir = os.path.join(save_dir, 'pic/earnings')
        os.makedirs(earnings_dir, exist_ok=True)
        save_path = os.path.join(earnings_dir, f'{ticker}_{model_type}_cumulative.png')
        plt.savefig(save_path)
        plt.close()
    
        return save_path
    except Exception as e:
        print(f"Error plotting cumulative earnings for {ticker}: {e}")
        plt.close()
        return None

def plot_accuracy_comparison(lstm_metrics, gru_metrics, save_dir):
    """
    绘制所有股票在LSTM和GRU模型上的预测准确度分组对比图。
    
    参数:
        lstm_metrics: 包含每个股票在LSTM上预测指标的字典
        gru_metrics: 包含每个股票在GRU上预测指标的字典
        save_dir: 图片保存的根目录
    返回:
        str: 保存的图片路径
    """
    try:
        if not lstm_metrics or not gru_metrics:
            print("Metrics for one or both models are missing.")
            return None
        
        # 确保 tickers 对齐
        tickers = sorted(list(lstm_metrics.keys()))
        lstm_acc = [lstm_metrics[t]['accuracy'] * 100 for t in tickers]
        gru_acc = [gru_metrics.get(t, {'accuracy': 0})['accuracy'] * 100 for t in tickers]

        x = np.arange(len(tickers))  # the label locations
        width = 0.35  # the width of the bars

        fig, ax = plt.subplots(figsize=(18, 7))
        rects1 = ax.bar(x - width/2, lstm_acc, width, label='LSTM')
        rects2 = ax.bar(x + width/2, gru_acc, width, label='GRU')

        # Add some text for labels, title and axes ticks
        ax.set_ylabel('Accuracy (%)')
        ax.set_title('Prediction Accuracy Comparison: LSTM vs. GRU')
        ax.set_xticks(x)
        ax.set_xticklabels(tickers, rotation=45, ha="right")
        ax.legend()
        ax.grid(True, axis='y', linestyle='--', alpha=0.6)

        # Optional: Add data labels on top of bars
        ax.bar_label(rects1, padding=3, fmt='%.1f')
        ax.bar_label(rects2, padding=3, fmt='%.1f')

        fig.tight_layout()

        prediction_dir = os.path.join(save_dir, 'pic')
        os.makedirs(prediction_dir, exist_ok=True)
        save_path = os.path.join(prediction_dir, 'accuracy_comparison_grouped.png')
        plt.savefig(save_path)
        plt.close()

        return save_path
    except Exception as e:
        print(f"Error plotting accuracy comparison: {e}")
        plt.close()
        return None

def plot_trading_result(ticker, close_prices, states_buy, states_sell, total_gains, invest, save_dir):
    """
    绘制交易结果图表
    
    参数:
        ticker: 股票代码
        close_prices: 收盘价列表
        states_buy: 买入点列表
        states_sell: 卖出点列表
        total_gains: 总收益
        invest: 投资回报率
        save_dir: 保存路径
    返回:
        str: 保存的图片路径
    """
    try:
        plt.figure(figsize=(15, 5))
        plt.plot(close_prices, color='r', lw=2.)
        plt.plot(close_prices, '^', markersize=10, color='m', label='buying signal', markevery=states_buy)
        plt.plot(close_prices, 'v', markersize=10, color='k', label='selling signal', markevery=states_sell)
        plt.title(f'{ticker} total gains ${total_gains:.2f}, total investment {invest:.2f}%')
        plt.legend()
    
        # 创建保存目录
        trades_dir = os.path.join(save_dir, 'pic/trades')
        os.makedirs(trades_dir, exist_ok=True)
    
        # 保存图片
        save_path = os.path.join(trades_dir, f'{ticker}_trades.png')
        plt.savefig(save_path)
        plt.close()
    
        return save_path
    except Exception as e:
        print(f"Error plotting trading result for {ticker}: {e}")
        plt.close()
        return None
