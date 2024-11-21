#!/usr/bin/env python
# coding: utf-8

# In[2]:


from dash import Dash, dcc, html, Input, Output, State
from waitress import serve
import dash
import pandas as pd
import plotly.graph_objects as go
import io
import os
import base64
from dash.exceptions import PreventUpdate


# In[13]:


# 初始空的 DataFrame
df = pd.DataFrame()
# 建立 Dash 應用程式
app = Dash(__name__)
server = app.server  # 确保有这行
# 初始圖表為年度總盈利圖
def create_annual_chart():
    if df.empty:
        fig = go.Figure()
        fig.update_layout(title='尚未載入資料', xaxis_title='年份', yaxis_title='盈利')
    else:
        annual_profit = df.groupby('年')['盈利'].sum()
        fig = go.Figure()
        fig.add_trace(go.Bar(x=annual_profit.index, y=annual_profit.values, name='年度總盈利'))
        fig.add_trace(go.Scatter(x=annual_profit.index, y=annual_profit.values, mode='lines+markers', name='年度盈利趨勢'))
        fig.update_layout(title='每年總盈利', xaxis_title='年份', yaxis_title='盈利')
    return fig

# 應用程式的佈局
app.layout = html.Div([
    html.Div([
        dcc.Upload(
            id='upload-data',
            children=html.Button('匯入 Excel', style={'font-size': '16px', 'padding': '10px'}),
            multiple=False
        ),
        html.Button('返回', id='back-button', n_clicks=0, style={'font-size': '16px', 'padding': '10px', 'margin-left': '10px'})
    ], style={'display': 'flex', 'align-items': 'center', 'padding': '10px'}),
    dcc.Graph(id='profit-chart', figure=create_annual_chart()),
    html.Div(id='selected-year', style={'display': 'none'}),
    html.Div(id='selected-month', style={'display': 'none'}),
    html.Div(id='selected-week', style={'display': 'none'}),
    html.Div(id='graph-level', children='annual', style={'display': 'none'}),
    html.Div(id='order-list')
])

# 合併後的回調函數
@app.callback(
    Output('profit-chart', 'figure'),
    Output('selected-year', 'children'),
    Output('selected-month', 'children'),
    Output('selected-week', 'children'),
    Output('order-list', 'children'),
    Output('graph-level', 'children'),
    Input('upload-data', 'contents'),
    Input('profit-chart', 'clickData'),
    Input('back-button', 'n_clicks'),
    State('selected-year', 'children'),
    State('selected-month', 'children'),
    State('selected-week', 'children'),
    State('graph-level', 'children')
)
def update_chart(contents, clickData, n_clicks, selected_year, selected_month, selected_week, graph_level):
    global df  # 使用全域變數
    ctx = dash.callback_context
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else None

    # 上傳檔案的處理
    if triggered_id == 'upload-data' and contents is not None:
        content_type, content_string = contents.split(',')
        decoded = io.BytesIO(base64.b64decode(content_string))
        df = pd.read_excel(decoded)

        # 資料處理
        df = df.loc[df['趨勢'] == 'out']
        df.sort_values(by='時間' , ascending=True)
        df['時間'] = pd.to_datetime(df['時間'])
        df['年'] = df['時間'].dt.year
        df['月'] = df['時間'].dt.month
        df['周'] = df['時間'].dt.isocalendar().week

        return create_annual_chart(), None, None, None, dash.no_update, 'annual'
        # 返回按鈕點擊處理
    if triggered_id == 'back-button' and n_clicks > 0:
        if graph_level == 'monthly':
            return create_annual_chart(), None, None, None, dash.no_update, 'annual'
        elif graph_level == 'weekly':
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
        clicked_data = clickData['points'][0]['x']
        clicked_curve = clickData['points'][0]['curveNumber']

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

    return create_annual_chart(), None, None, None, dash.no_update, 'annual'


# In[15]:


# 定義回調函數
# 當圖表中的不同層次的柱狀圖被點擊時，圖表會根據需求進行更新

# 最後一行
if __name__ == '__main__':
    app.run_server(port=8051)

