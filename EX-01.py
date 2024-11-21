#!/usr/bin/env python
# coding: utf-8

# In[1]:


import dash
import pandas as pd
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output, State
import os

# 假設交易數據在一個名為 df 的 DataFrame 中
# 載入數據
date = pd.read_excel('EX.xlsx')


# In[2]:


df=date.loc[date['趨勢'] == 'out']
df.sort_values(by='時間' , ascending=True)


# In[3]:


df['時間'] = pd.to_datetime(df['時間'])   # 將「時間」欄位轉換為日期時間格式
df['年'] = df['時間'].dt.year             # 從「時間」欄位提取年份，並新增一欄儲存
df['月'] = df['時間'].dt.month            # 從「時間」欄位提取月份，並新增一欄儲存
df['周'] = df['時間'].dt.isocalendar().week  # 從「時間」欄位提取週次，並新增一欄儲存

# 計算每年總盈利
annual_profit = df.groupby('年')['盈利'].sum()  # 根據「年」分組並計算「盈利」欄位的總和

# 建立 Dash 應用程式
app = Dash(__name__)   # 創建一個 Dash 應用程序實例

# 初始圖表為年度總盈利圖
def create_annual_chart():
    fig = go.Figure()   # 建立一個空的圖形對象
    fig.add_trace(go.Bar(x=annual_profit.index, y=annual_profit.values, name='年度總盈利'))  # 添加年度總盈利的柱狀圖
    fig.add_trace(go.Scatter(x=annual_profit.index, y=annual_profit.values, mode='lines+markers', name='年度盈利趨勢'))  # 添加年度盈利趨勢的折線圖
    fig.update_layout(title='每年總盈利', xaxis_title='年份', yaxis_title='盈利')  # 設定圖表標題和 x、y 軸標題
    return fig   # 返回圖表對象

# 應用程式的佈局
app.layout = html.Div([
    dcc.Graph(id='profit-chart', figure=create_annual_chart()),   # 繪製年度總盈利圖
    html.Div(id='selected-year', style={'display': 'none'}),      # 隱藏選定年份的儲存元素
    html.Div(id='selected-month', style={'display': 'none'}),     # 隱藏選定月份的儲存元素
    html.Div(id='selected-week', style={'display': 'none'}),      # 隱藏選定週次的儲存元素
    html.Div(id='graph-level', children='annual', style={'display': 'none'}),  # 隱藏圖表層級的儲存元素，初始為年度層級
    html.Div(id='order-list'),     # 顯示每筆訂單的區域
    html.Button('返回', id='back-button', n_clicks=0, style={'position': 'absolute', 'top': '10px', 'left': '10px'})  # 返回按鈕，設置在左上角
])

# 更新圖表的回調函數
@app.callback(
    Output('profit-chart', 'figure'),            # 更新圖表
    Output('selected-year', 'children'),         # 更新選定的年份
    Output('selected-month', 'children'),        # 更新選定的月份
    Output('selected-week', 'children'),         # 更新選定的週次
    Output('order-list', 'children'),            # 更新訂單列表
    Output('graph-level', 'children'),           # 更新圖表層級
    Input('profit-chart', 'clickData'),          # 圖表的點擊數據輸入
    Input('back-button', 'n_clicks'),            # 返回按鈕的點擊次數輸入
    State('selected-year', 'children'),          # 讀取選定年份的狀態
    State('selected-month', 'children'),         # 讀取選定月份的狀態
    State('selected-week', 'children'),          # 讀取選定週次的狀態
    State('graph-level', 'children')             # 讀取當前圖表層級的狀態
)
def update_chart(clickData, n_clicks, selected_year, selected_month, selected_week, graph_level):
    ctx = dash.callback_context                             # 獲取回調上下文，判斷觸發的輸入元件
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else None  # 獲取觸發元素的 ID

    # 返回按鈕點擊處理
    if triggered_id == 'back-button' and n_clicks > 0:
        if graph_level == 'monthly':   # 如果目前為月度層級，返回年度總盈利圖
            return create_annual_chart(), None, None, None, dash.no_update, 'annual'
        elif graph_level == 'weekly':  # 如果目前為週層級，返回月度盈利圖
            yearly_data = df[df['年'] == selected_year]
            monthly_positive_profit = yearly_data[yearly_data['盈利'] > 0].groupby('月')['盈利'].sum()
            monthly_negative_profit = yearly_data[yearly_data['盈利'] < 0].groupby('月')['盈利'].sum()
            monthly_total_profit = yearly_data.groupby('月')['盈利'].sum()
            fig = go.Figure()
            fig.add_trace(go.Bar(x=monthly_total_profit.index, y=monthly_positive_profit.reindex(monthly_total_profit.index, fill_value=0), name='當月正盈利'))
            fig.add_trace(go.Bar(x=monthly_total_profit.index, y=monthly_negative_profit.reindex(monthly_total_profit.index, fill_value=0), name='當月負盈利'))
            fig.add_trace(go.Bar(x=monthly_total_profit.index, y=monthly_total_profit.values, name='當月總盈利'))
            fig.update_layout(title=f'{selected_year}年每月盈利', xaxis_title='月份', yaxis_title='盈利', barmode='group')
            return fig, selected_year, None, None, dash.no_update, 'monthly'
        elif graph_level == 'order_list':  # 如果目前為訂單列表層級，返回週盈利圖
            monthly_data = df[(df['年'] == selected_year) & (df['月'] == selected_month)]
            weekly_positive_profit = monthly_data[monthly_data['盈利'] > 0].groupby('周')['盈利'].sum()
            weekly_negative_profit = monthly_data[monthly_data['盈利'] < 0].groupby('周')['盈利'].sum()
            weekly_total_profit = monthly_data.groupby('周')['盈利'].sum()
            fig = go.Figure()
            # 使用時間範圍作為 X 軸標籤
            fig.add_trace(go.Bar(x=weekly_total_profit.index, y=weekly_positive_profit.reindex(weekly_total_profit.index, fill_value=0), name='當周正盈利'))
            fig.add_trace(go.Bar(x=weekly_total_profit.index, y=weekly_negative_profit.reindex(weekly_total_profit.index, fill_value=0), name='當周負盈利'))
            fig.add_trace(go.Bar(x=weekly_total_profit.index, y=weekly_total_profit.values, name='當周總盈利'))
            fig.update_layout(title=f'{selected_year}年{selected_month}月每周盈利', xaxis_title='周', yaxis_title='盈利', barmode='group')
            return fig, selected_year, selected_month, None, dash.no_update, 'weekly'

    # 處理點擊圖表進入下一層
    if clickData:
        clicked_data = clickData['points'][0]['x']  # 獲取點擊的 x 軸值
        clicked_curve = clickData['points'][0]['curveNumber']  # 獲取點擊的圖層（正盈利、負盈利或總盈利）

        # 如果目前在年度層級，點擊後進入月度層級
        if graph_level == 'annual':
            selected_year = clicked_data
            yearly_data = df[df['年'] == selected_year]
            monthly_positive_profit = yearly_data[yearly_data['盈利'] > 0].groupby('月')['盈利'].sum()
            monthly_negative_profit = yearly_data[yearly_data['盈利'] < 0].groupby('月')['盈利'].sum()
            monthly_total_profit = yearly_data.groupby('月')['盈利'].sum()
            fig = go.Figure()
            fig.add_trace(go.Bar(x=monthly_total_profit.index, y=monthly_positive_profit.reindex(monthly_total_profit.index, fill_value=0), name='當月正盈利'))
            fig.add_trace(go.Bar(x=monthly_total_profit.index, y=monthly_negative_profit.reindex(monthly_total_profit.index, fill_value=0), name='當月負盈利'))
            fig.add_trace(go.Bar(x=monthly_total_profit.index, y=monthly_total_profit.values, name='當月總盈利'))
            fig.update_layout(title=f'{selected_year}年每月盈利', xaxis_title='月份', yaxis_title='盈利', barmode='group')
            return fig, selected_year, None, None, dash.no_update, 'monthly'

        # 如果目前在月度層級，點擊後進入每周層級
        elif graph_level == 'monthly':
            selected_month = clicked_data
            monthly_data = df[(df['年'] == selected_year) & (df['月'] == selected_month)]
            weekly_positive_profit = monthly_data[monthly_data['盈利'] > 0].groupby('周')['盈利'].sum()
            weekly_negative_profit = monthly_data[monthly_data['盈利'] < 0].groupby('周')['盈利'].sum()
            weekly_total_profit = monthly_data.groupby('周')['盈利'].sum()
            fig = go.Figure()
            fig.add_trace(go.Bar(x=weekly_total_profit.index, y=weekly_positive_profit.reindex(weekly_total_profit.index, fill_value=0), name='當周正盈利'))
            fig.add_trace(go.Bar(x=weekly_total_profit.index, y=weekly_negative_profit.reindex(weekly_total_profit.index, fill_value=0), name='當周負盈利'))
            fig.add_trace(go.Bar(x=weekly_total_profit.index, y=weekly_total_profit.values, name='當周總盈利'))
            fig.update_layout(title=f'{selected_year}年{selected_month}月每周盈利', xaxis_title='周', yaxis_title='盈利', barmode='group')
            return fig, selected_year, selected_month, None, dash.no_update, 'weekly'

        # 如果目前在每周層級，點擊後顯示該周每筆訂單，根據圖層篩選正負盈利
        elif graph_level == 'weekly':
            selected_week = clicked_data  # 獲取點擊的周次
            weekly_data = df[(df['年'] == selected_year) & (df['月'] == selected_month) & (df['周'] == selected_week)]

            # 根據點擊的柱狀圖，篩選顯示正盈利、負盈利或全部訂單
            if clicked_curve == 0:  # 正盈利柱狀圖
                weekly_data = weekly_data[weekly_data['盈利'] > 0]
            elif clicked_curve == 1:  # 負盈利柱狀圖
                weekly_data = weekly_data[weekly_data['盈利'] < 0]

            # 將每筆訂單轉換為表格格式
            orders_list = weekly_data[['時間', '交易品種', '類型', '價位', '盈利']].to_dict('records')

            # 使用 HTML 表格來顯示每筆交易訂單，添加框線樣式
            orders_html = html.Table([
                html.Tr([html.Th(col) for col in ['時間', '交易品種', '類型', '價位', '盈利']]),  # 表格標題
                *[html.Tr([html.Td(order[col], style={'border': '1px solid black'}) for col in ['時間', '交易品種', '類型', '價位', '盈利']]) for order in orders_list]  # 訂單資料
            ], style={'border-collapse': 'collapse', 'width': '100%', 'border': '1px solid black'})  # 設定表格的框線樣式

            # 返回更新的內容到 order-list，並將圖層更新為 'order_list'
            return dash.no_update, selected_year, selected_month, selected_week, orders_html, 'weekly'

    return create_annual_chart(), None, None, None, dash.no_update, 'annual'  # 預設返回年度圖表

    


# In[8]:


# 定義回調函數
# 當圖表中的不同層次的柱狀圖被點擊時，圖表會根據需求進行更新

# 最後一行
if __name__ == '__main__':
    app.run_server(port=8051)


# In[ ]:




