from time import sleep

import gradio as gr

import requests

def query(text):
    ret = ''
    res = requests.post('http://127.0.0.1:8000/re/query', json={'text': text})
    data = res.json()
    task_id = data['id']
    while True:
        res = requests.get(f'http://127.0.0.1:8000/re/query/status/{task_id}')
        task_state = res.json()
        if task_state['state'] == 1:
            ret = task_state['data']['response']
            break
        elif task_state['state'] == 2:
            ret = 'Failed'
            break
        else:
            sleep(1)
            continue
    return ret

demo = gr.Interface(
    fn=query,
    inputs=["text"],
    outputs=["text"],
)

demo.launch()