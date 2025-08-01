import gradio as gr
import pandas as pd
import torch
import os
from PIL import Image
import warnings
import yfinance as yf
from model import predict, format_feature
from RLagent import process_stock
from datetime import datetime
from process_stock_data import get_stock_data, clean_csv_files

# 禁用代理（如需代理请取消注释）
# os.environ['HTTP_PROXY'] = 'http://127.0.0.1:7890'
# os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:7890'
os.environ['NO_PROXY'] = 'localhost,127.0.0.1'

warnings.filterwarnings("ignore")
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

SAVE_DIR = os.path.join(os.getcwd(), 'results')
os.makedirs(SAVE_DIR, exist_ok=True)
os.makedirs(os.path.join(SAVE_DIR, 'pic'), exist_ok=True)
os.makedirs(os.path.join(SAVE_DIR, 'ticker'), exist_ok=True)

# 自定义CSS（略，与原文件一致）

custom_css = """
.gradio-container {
    background-color: #f0f7ff;
}
.gr-button {
    background-color: #4a90e2;
    color: white;
    border: none;
    border-radius: 8px;
    transition: all 0.3s ease;
}
.gr-button:hover {
    background-color: #357abd;
    transform: translateY(-2px);
}
.gr-button:active {
    transform: translateY(0);
}
"""

def get_data(ticker, start_date, end_date, progress=gr.Progress()):
    data_folder = os.path.join(SAVE_DIR, 'ticker')
    temp_path = f'{data_folder}/{ticker}.csv'

    try:
        progress(0, desc="Start obtaining stock data...")
        stock_data = get_stock_data(ticker, start_date, end_date)
        progress(0.4, desc="Calculate technical indicators...")
        stock_data.to_csv(temp_path)
        progress(0.7, desc="Processing data format...")
        clean_csv_files(temp_path)
        progress(1.0, desc="Data acquisition completed")
        return temp_path, f'<span class="status-success">Data acquisition successful</span>'
    except Exception as e:
        return None, f'<span class="status-error">Error in obtaining data: {str(e)}</span>'

def process_and_predict(temp_csv_path, model_type,
                       lstm_epochs, lstm_batch, lstm_learning_rate,
                       gru_epochs, gru_batch, gru_learning_rate,
                       window_size, initial_money, agent_iterations, save_dir):
    if not temp_csv_path:
        return [None] * 9

    try:
        ticker = os.path.basename(temp_csv_path).split('.')[0]
        stock_data = pd.read_csv(temp_csv_path)
        stock_features = format_feature(stock_data)

        if model_type == "LSTM":
            epochs, batch_size, learning_rate = lstm_epochs, lstm_batch, lstm_learning_rate
        else:
            epochs, batch_size, learning_rate = gru_epochs, gru_batch, gru_learning_rate

        # 调用模型预测
        metrics = predict(
            save_dir=save_dir,
            ticker_name=ticker,
            stock_data=stock_data,
            stock_features=stock_features,
            model_type=model_type,
            epochs=epochs,
            batch_size=batch_size,
            learning_rate=learning_rate
        )

        # 调用交易代理
        trading_results = process_stock(
            ticker,
            save_dir,
            model_type,
            window_size=window_size,
            initial_money=initial_money,
            iterations=agent_iterations
        )

        # ✅ 修复：统一使用 model_type 作为文件名一部分
        prediction_plot = Image.open(f"{save_dir}/pic/predictions/{ticker}_{model_type}_prediction.png")
        loss_plot = Image.open(f"{save_dir}/pic/loss/{ticker}_{model_type}_loss.png")
        earnings_plot = Image.open(f"{save_dir}/pic/earnings/{ticker}_{model_type}_cumulative.png")
        trades_plot = Image.open(f"{save_dir}/pic/trades/{ticker}_{model_type}_trades.png")
        transactions_df = pd.read_csv(f"{save_dir}/transactions/{ticker}_{model_type}_transactions.csv")

        return [
            [prediction_plot, loss_plot, earnings_plot, trades_plot],
            metrics['accuracy'] * 100,
            metrics['rmse'],
            metrics['mae'],
            trading_results['total_gains'],
            trading_results['investment_return'],
            trading_results['trades_buy'],
            trading_results['trades_sell'],
            transactions_df
        ]
    except Exception as e:
        print(f"[ERROR] process_and_predict failed: {e}")
        return [None] * 9

# ✅ Gradio UI 保持不变
with gr.Blocks(css=custom_css, theme=gr.themes.Soft()) as demo:
    gr.Markdown("# Intelligent Stock Prediction and Trading Agent")

    save_dir_state = gr.State(value=SAVE_DIR)
    temp_csv_state = gr.State(value=None)

    with gr.Row():
        with gr.Column(scale=2):
            ticker_input = gr.Textbox(label="Stock code", placeholder="Enter stock symbol (e.g., AAPL)")
        with gr.Column(scale=2):
            start_date = gr.Textbox(
                label="Start date (YYYY-MM-DD)",
                value=(datetime.now().replace(year=datetime.now().year-4).strftime('%Y-%m-%d'))
            )
        with gr.Column(scale=2):
            end_date = gr.Textbox(
                label="End date (YYYY-MM-DD)",
                value=datetime.now().strftime('%Y-%m-%d')
            )
        with gr.Column(scale=1):
            fetch_button = gr.Button("Get data", variant="primary")

    with gr.Row():
        status_output = gr.HTML(label="Status information")

    with gr.Row():
        data_file = gr.File(label="Download stock data", visible=True, interactive=False)

    with gr.Row():
        model_selector = gr.Dropdown(
            choices=["LSTM", "GRU"],
            label="Prediction Model",
            value="LSTM",
            info="Select the model to use for stock price prediction",
            multiselect=False
        )

    with gr.Tabs():
        with gr.TabItem("LSTM Prediction parameters") as lstm_tab:
            lstm_epochs = gr.Slider(minimum=100, maximum=1000, value=500, step=10, label="LSTM Training rounds")
            lstm_batch = gr.Slider(minimum=16, maximum=128, value=32, step=16, label="LSTM Batch size")
            lstm_learning_rate = gr.Slider(minimum=0.0001, maximum=0.01, value=0.001, step=0.0001, label="LSTM Learning rate")

        with gr.TabItem("GRU Prediction parameters") as gru_tab:
            gru_epochs = gr.Slider(minimum=100, maximum=1000, value=500, step=10, label="GRU Training rounds")
            gru_batch = gr.Slider(minimum=16, maximum=128, value=32, step=16, label="GRU Batch size")
            gru_learning_rate = gr.Slider(minimum=0.0001, maximum=0.01, value=0.001, step=0.0001, label="GRU Learning rate")

        with gr.TabItem("Trading agent parameters"):
            window_size = gr.Slider(minimum=10, maximum=100, value=30, step=5, label="Time window size")
            initial_money = gr.Number(value=10000, label="Initial investment amount ($)")
            agent_iterations = gr.Slider(minimum=100, maximum=1000, value=500, step=50, label="Agent training iterations")

    with gr.Row():
        train_button = gr.Button("Start training", variant="primary", interactive=False)

    with gr.Row():
        output_gallery = gr.Gallery(label="Analysis results visualization", show_label=True,
                                  elem_id="gallery", columns=4, rows=1, height="auto", object_fit="contain")

    with gr.Row():
        with gr.Column():
            accuracy = gr.Number(label="Accuracy (%)")
            rmse = gr.Number(label="RMSE")
            mae = gr.Number(label="MAE")
        with gr.Column():
            total_gains = gr.Number(label="Total Gains ($)")
            investment_return = gr.Number(label="Return Rate (%)")
            trades_buy = gr.Number(label="Buy Trades")
            trades_sell = gr.Number(label="Sell Trades")

    with gr.Row():
        transactions_df = gr.Dataframe(label="Transaction History")

    def update_interface(csv_path):
        return csv_path if csv_path else None, gr.update(interactive=bool(csv_path))

    def update_model_tabs(model_type):
        if model_type == "LSTM":
            return gr.update(visible=True), gr.update(visible=False)
        else:
            return gr.update(visible=False), gr.update(visible=True)

    model_selector.change(fn=update_model_tabs, inputs=[model_selector], outputs=[lstm_tab, gru_tab])

    fetch_result = fetch_button.click(
        fn=get_data,
        inputs=[ticker_input, start_date, end_date],
        outputs=[temp_csv_state, status_output]
    )

    fetch_result.then(update_interface, inputs=[temp_csv_state], outputs=[data_file, train_button])

    train_button.click(
        fn=process_and_predict,
        inputs=[
            temp_csv_state,
            model_selector,
            lstm_epochs, lstm_batch, lstm_learning_rate,
            gru_epochs, gru_batch, gru_learning_rate,
            window_size, initial_money, agent_iterations, save_dir_state
        ],
        outputs=[
            output_gallery,
            accuracy, rmse, mae,
            total_gains, investment_return, trades_buy, trades_sell,
            transactions_df
        ]
    )

demo.launch(server_port=7860, share=True)