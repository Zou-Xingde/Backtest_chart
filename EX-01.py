#!/usr/bin/env python
# coding: utf-8

# In[4]:


from dash import Dash, html, dcc, Input, Output, State, dash_table
import pandas as pd

# 創建 Dash 應用
app = Dash(__name__)
server = app.server  # 确保有这行
app.title = "Excel Viewer"

# 定義應用佈局
app.layout = html.Div([
    html.H1("Excel 文件查看器", style={"textAlign": "center"}),
    dcc.Upload(
        id="upload-data",
        children=html.Div([
            "拖曳或點擊上傳 Excel 文件"
        ]),
        style={
            "width": "100%",
            "height": "60px",
            "lineHeight": "60px",
            "borderWidth": "1px",
            "borderStyle": "dashed",
            "borderRadius": "5px",
            "textAlign": "center",
            "margin": "10px",
        },
        multiple=False
    ),
    html.Div(id="output-data", style={"marginTop": "20px"})
])

# 處理文件上傳並顯示內容
@app.callback(
    Output("output-data", "children"),
    [Input("upload-data", "contents")],
    [State("upload-data", "filename")]
)
def update_output(contents, filename):
    if contents is None:
        return "請上傳一個 Excel 文件。"

    # 處理上傳的內容
    content_type, content_string = contents.split(',')
    try:
        # 讀取上傳的 Excel 文件
        if filename.endswith(".xlsx") or filename.endswith(".xls"):
            import io
            import base64
            decoded = base64.b64decode(content_string)
            df = pd.read_excel('EX.xlsx')
            # 返回表格視圖
            return dash_table.DataTable(
                data=df.to_dict("records"),
                columns=[{"name": col, "id": col} for col in df.columns],
                page_size=10,  # 每頁顯示的行數
                style_table={"overflowX": "auto"},
                style_cell={"textAlign": "left"},
            )
        else:
            return html.Div("請上傳有效的 Excel 文件（.xlsx 或 .xls）。")
    except Exception as e:
        return html.Div(f"無法處理文件: {e}")


# In[6]:


# 定義回調函數
# 當圖表中的不同層次的柱狀圖被點擊時，圖表會根據需求進行更新

# 最後一行
if __name__ == '__main__':
    app.run_server(port=8051)


# In[ ]:




