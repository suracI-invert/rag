from time import sleep

import gradio as gr

import requests

BACKEND = "http://backend:80/"

def query(text):
    ret = ''
    res = requests.post(f'{BACKEND}re/query', json={'text': text})
    data = res.json()
    task_id = data['id']
    while True:
        res = requests.get(f'{BACKEND}re/query/status/{task_id}')
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

if __name__ == '__main__':
    demo.launch(server_name='0.0.0.0', server_port=7000)