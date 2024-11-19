{
 "cells": [
  {
   "cell_type": "code",
   "execution_count": 71,
   "id": "d917dd95-2d26-4bc9-96d9-98fdbd2b2616",
   "metadata": {},
   "outputs": [],
   "source": [
    "from dash import Dash, dcc, html, Input, Output, State\n",
    "import dash\n",
    "import pandas as pd\n",
    "import plotly.graph_objects as go\n",
    "import io\n",
    "import base64\n",
    "from dash.exceptions import PreventUpdate\n",
    "\n",
    "# 初始空的 DataFrame\n",
    "df = pd.DataFrame()\n",
    "\n",
    "# 建立 Dash 應用程式\n",
    "app = Dash(__name__)\n",
    "\n",
    "# 初始圖表為年度總盈利圖\n",
    "def create_annual_chart():\n",
    "    if df.empty:\n",
    "        fig = go.Figure()\n",
    "        fig.update_layout(title='尚未載入資料', xaxis_title='年份', yaxis_title='盈利')\n",
    "    else:\n",
    "        annual_profit = df.groupby('年')['盈利'].sum()\n",
    "        fig = go.Figure()\n",
    "        fig.add_trace(go.Bar(x=annual_profit.index, y=annual_profit.values, name='年度總盈利'))\n",
    "        fig.add_trace(go.Scatter(x=annual_profit.index, y=annual_profit.values, mode='lines+markers', name='年度盈利趨勢'))\n",
    "        fig.update_layout(title='每年總盈利', xaxis_title='年份', yaxis_title='盈利')\n",
    "    return fig\n",
    "\n",
    "# 應用程式的佈局\n",
    "app.layout = html.Div([\n",
    "    html.Div([\n",
    "        dcc.Upload(\n",
    "            id='upload-data',\n",
    "            children=html.Button('匯入 Excel', style={'font-size': '16px', 'padding': '10px'}),\n",
    "            multiple=False\n",
    "        ),\n",
    "        html.Button('返回', id='back-button', n_clicks=0, style={'font-size': '16px', 'padding': '10px', 'margin-left': '10px'})\n",
    "    ], style={'display': 'flex', 'align-items': 'center', 'padding': '10px'}),\n",
    "    dcc.Graph(id='profit-chart', figure=create_annual_chart()),\n",
    "    html.Div(id='selected-year', style={'display': 'none'}),\n",
    "    html.Div(id='selected-month', style={'display': 'none'}),\n",
    "    html.Div(id='selected-week', style={'display': 'none'}),\n",
    "    html.Div(id='graph-level', children='annual', style={'display': 'none'}),\n",
    "    html.Div(id='order-list')\n",
    "])\n",
    "\n",
    "# 合併後的回調函數\n",
    "@app.callback(\n",
    "    Output('profit-chart', 'figure'),\n",
    "    Output('selected-year', 'children'),\n",
    "    Output('selected-month', 'children'),\n",
    "    Output('selected-week', 'children'),\n",
    "    Output('order-list', 'children'),\n",
    "    Output('graph-level', 'children'),\n",
    "    Input('upload-data', 'contents'),\n",
    "    Input('profit-chart', 'clickData'),\n",
    "    Input('back-button', 'n_clicks'),\n",
    "    State('selected-year', 'children'),\n",
    "    State('selected-month', 'children'),\n",
    "    State('selected-week', 'children'),\n",
    "    State('graph-level', 'children')\n",
    ")\n",
    "def update_chart(contents, clickData, n_clicks, selected_year, selected_month, selected_week, graph_level):\n",
    "    global df  # 使用全域變數\n",
    "    ctx = dash.callback_context\n",
    "    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else None\n",
    "\n",
    "    # 上傳檔案的處理\n",
    "    if triggered_id == 'upload-data' and contents is not None:\n",
    "        content_type, content_string = contents.split(',')\n",
    "        decoded = io.BytesIO(base64.b64decode(content_string))\n",
    "        df = pd.read_excel(decoded)\n",
    "\n",
    "        # 資料處理\n",
    "        df = df.loc[df['趨勢'] == 'out']\n",
    "        df.sort_values(by='時間' , ascending=True)\n",
    "        df['時間'] = pd.to_datetime(df['時間'])\n",
    "        df['年'] = df['時間'].dt.year\n",
    "        df['月'] = df['時間'].dt.month\n",
    "        df['周'] = df['時間'].dt.isocalendar().week\n",
    "\n",
    "        return create_annual_chart(), None, None, None, dash.no_update, 'annual'\n",
    "\n",
    "    # 返回按鈕點擊處理\n",
    "    if triggered_id == 'back-button' and n_clicks > 0:\n",
    "        if graph_level == 'monthly':\n",
    "            return create_annual_chart(), None, None, None, dash.no_update, 'annual'\n",
    "        elif graph_level == 'weekly':\n",
    "            yearly_data = df[df['年'] == selected_year]\n",
    "            monthly_positive_profit = yearly_data[yearly_data['盈利'] > 0].groupby('月')['盈利'].sum()\n",
    "            monthly_negative_profit = yearly_data[yearly_data['盈利'] < 0].groupby('月')['盈利'].sum()\n",
    "            monthly_total_profit = yearly_data.groupby('月')['盈利'].sum()\n",
    "            fig = go.Figure()\n",
    "            fig.add_trace(go.Bar(x=monthly_total_profit.index, y=monthly_positive_profit.reindex(monthly_total_profit.index, fill_value=0), name='當月正盈利'))\n",
    "            fig.add_trace(go.Bar(x=monthly_total_profit.index, y=monthly_negative_profit.reindex(monthly_total_profit.index, fill_value=0), name='當月負盈利'))\n",
    "            fig.add_trace(go.Bar(x=monthly_total_profit.index, y=monthly_total_profit.values, name='當月總盈利'))\n",
    "            fig.update_layout(title=f'{selected_year}年每月盈利', xaxis_title='月份', yaxis_title='盈利', barmode='group')\n",
    "            return fig, selected_year, None, None, dash.no_update, 'monthly'\n",
    "        elif graph_level == 'order_list':  # 如果目前為訂單列表層級，返回週盈利圖\n",
    "            monthly_data = df[(df['年'] == selected_year) & (df['月'] == selected_month)]\n",
    "            weekly_positive_profit = monthly_data[monthly_data['盈利'] > 0].groupby('周')['盈利'].sum()\n",
    "            weekly_negative_profit = monthly_data[monthly_data['盈利'] < 0].groupby('周')['盈利'].sum()\n",
    "            weekly_total_profit = monthly_data.groupby('周')['盈利'].sum()\n",
    "            fig = go.Figure()\n",
    "            # 使用時間範圍作為 X 軸標籤\n",
    "            fig.add_trace(go.Bar(x=weekly_total_profit.index, y=weekly_positive_profit.reindex(weekly_total_profit.index, fill_value=0), name='當周正盈利'))\n",
    "            fig.add_trace(go.Bar(x=weekly_total_profit.index, y=weekly_negative_profit.reindex(weekly_total_profit.index, fill_value=0), name='當周負盈利'))\n",
    "            fig.add_trace(go.Bar(x=weekly_total_profit.index, y=weekly_total_profit.values, name='當周總盈利'))\n",
    "            fig.update_layout(title=f'{selected_year}年{selected_month}月每周盈利', xaxis_title='周', yaxis_title='盈利', barmode='group')\n",
    "            return fig, selected_year, selected_month, None, dash.no_update, 'weekly'\n",
    "\n",
    "    # 處理點擊圖表進入下一層\n",
    "    if clickData:\n",
    "        clicked_data = clickData['points'][0]['x']\n",
    "        clicked_curve = clickData['points'][0]['curveNumber']\n",
    "\n",
    "        if graph_level == 'annual':\n",
    "            selected_year = clicked_data\n",
    "            yearly_data = df[df['年'] == selected_year]\n",
    "            monthly_positive_profit = yearly_data[yearly_data['盈利'] > 0].groupby('月')['盈利'].sum()\n",
    "            monthly_negative_profit = yearly_data[yearly_data['盈利'] < 0].groupby('月')['盈利'].sum()\n",
    "            monthly_total_profit = yearly_data.groupby('月')['盈利'].sum()\n",
    "            fig = go.Figure()\n",
    "            fig.add_trace(go.Bar(x=monthly_total_profit.index, y=monthly_positive_profit.reindex(monthly_total_profit.index, fill_value=0), name='當月正盈利'))\n",
    "            fig.add_trace(go.Bar(x=monthly_total_profit.index, y=monthly_negative_profit.reindex(monthly_total_profit.index, fill_value=0), name='當月負盈利'))\n",
    "            fig.add_trace(go.Bar(x=monthly_total_profit.index, y=monthly_total_profit.values, name='當月總盈利'))\n",
    "            fig.update_layout(title=f'{selected_year}年每月盈利', xaxis_title='月份', yaxis_title='盈利', barmode='group')\n",
    "            return fig, selected_year, None, None, dash.no_update, 'monthly'\n",
    "        # 如果目前在月度層級，點擊後進入每周層級\n",
    "        elif graph_level == 'monthly':\n",
    "            selected_month = clicked_data\n",
    "            monthly_data = df[(df['年'] == selected_year) & (df['月'] == selected_month)]\n",
    "            weekly_positive_profit = monthly_data[monthly_data['盈利'] > 0].groupby('周')['盈利'].sum()\n",
    "            weekly_negative_profit = monthly_data[monthly_data['盈利'] < 0].groupby('周')['盈利'].sum()\n",
    "            weekly_total_profit = monthly_data.groupby('周')['盈利'].sum()\n",
    "            fig = go.Figure()\n",
    "            fig.add_trace(go.Bar(x=weekly_total_profit.index, y=weekly_positive_profit.reindex(weekly_total_profit.index, fill_value=0), name='當周正盈利'))\n",
    "            fig.add_trace(go.Bar(x=weekly_total_profit.index, y=weekly_negative_profit.reindex(weekly_total_profit.index, fill_value=0), name='當周負盈利'))\n",
    "            fig.add_trace(go.Bar(x=weekly_total_profit.index, y=weekly_total_profit.values, name='當周總盈利'))\n",
    "            fig.update_layout(title=f'{selected_year}年{selected_month}月每周盈利', xaxis_title='周', yaxis_title='盈利', barmode='group')\n",
    "            return fig, selected_year, selected_month, None, dash.no_update, 'weekly'\n",
    "        # 如果目前在每周層級，點擊後顯示該周每筆訂單，根據圖層篩選正負盈利\n",
    "        elif graph_level == 'weekly':\n",
    "            selected_week = clicked_data  # 獲取點擊的周次\n",
    "            weekly_data = df[(df['年'] == selected_year) & (df['月'] == selected_month) & (df['周'] == selected_week)]\n",
    "\n",
    "            # 根據點擊的柱狀圖，篩選顯示正盈利、負盈利或全部訂單\n",
    "            if clicked_curve == 0:  # 正盈利柱狀圖\n",
    "                weekly_data = weekly_data[weekly_data['盈利'] > 0]\n",
    "            elif clicked_curve == 1:  # 負盈利柱狀圖\n",
    "                weekly_data = weekly_data[weekly_data['盈利'] < 0]\n",
    "\n",
    "            # 將每筆訂單轉換為表格格式\n",
    "            orders_list = weekly_data[['時間', '交易品種', '類型', '價位', '盈利']].to_dict('records')\n",
    "\n",
    "            # 使用 HTML 表格來顯示每筆交易訂單，添加框線樣式\n",
    "            orders_html = html.Table([\n",
    "                html.Tr([html.Th(col) for col in ['時間', '交易品種', '類型', '價位', '盈利']]),  # 表格標題\n",
    "                *[html.Tr([html.Td(order[col], style={'border': '1px solid black'}) for col in ['時間', '交易品種', '類型', '價位', '盈利']]) for order in orders_list]  # 訂單資料\n",
    "            ], style={'border-collapse': 'collapse', 'width': '100%', 'border': '1px solid black'})  # 設定表格的框線樣式\n",
    "\n",
    "            # 返回更新的內容到 order-list，並將圖層更新為 'order_list'\n",
    "            return dash.no_update, selected_year, selected_month, selected_week, orders_html, 'weekly'\n",
    "\n",
    "    return create_annual_chart(), None, None, None, dash.no_update, 'annual'\n",
    "\n",
    "    server = app.server\n",
    "\n",
    "    if __name__ == '__main__':\n",
    "    app.run_server(debug=True)\n"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 4,
   "id": "1c6b126a-444d-4c53-be88-1e5309428ebf",
   "metadata": {},
   "outputs": [
    {
     "ename": "NameError",
     "evalue": "name 'python3' is not defined",
     "output_type": "error",
     "traceback": [
      "\u001b[1;31m---------------------------------------------------------------------------\u001b[0m",
      "\u001b[1;31mNameError\u001b[0m                                 Traceback (most recent call last)",
      "Cell \u001b[1;32mIn[4], line 1\u001b[0m\n\u001b[1;32m----> 1\u001b[0m python3 \u001b[38;5;241m-\u001b[39m\u001b[38;5;241m-\u001b[39mversion\n",
      "\u001b[1;31mNameError\u001b[0m: name 'python3' is not defined"
     ]
    }
   ],
   "source": [
    "python3 --version"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "id": "63f4a776-7e92-4060-8910-3705612555cd",
   "metadata": {},
   "outputs": [],
   "source": []
  }
 ],
 "metadata": {
  "kernelspec": {
   "display_name": "Python 3 (ipykernel)",
   "language": "python",
   "name": "python3"
  },
  "language_info": {
   "codemirror_mode": {
    "name": "ipython",
    "version": 3
   },
   "file_extension": ".py",
   "mimetype": "text/x-python",
   "name": "python",
   "nbconvert_exporter": "python",
   "pygments_lexer": "ipython3",
   "version": "3.12.4"
  }
 },
 "nbformat": 4,
 "nbformat_minor": 5
}
