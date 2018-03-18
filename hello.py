import pika, uuid, json
from flask import Flask, request, jsonify
app = Flask(__name__)

@app.route("/")
def hello():
    return "Hello World!"


def on_request(ch, method, props, body):
    ch.basic_publish(exchange='', routing_key=props.reply_to, properties=pika.BasicProperties(correlation_id=props.correlation_id), body=body)
    ch.basic_ack(delivery_tag=method.delivery_tag)

    
@app.route("/speak", methods=['GET', 'POST'])
def speak():
    if request.method == 'POST':
	data = request.get_json()

	key = data['key']
	msg = data['msg']
	connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
        channel = connection.channel()
  
        channel.exchange_declare(exchange='hw3', exchange_type='direct')
	channel.basic_publish(exchange='hw3', routing_key=key, body=msg)
	connection.close()
    	
        return jsonify({"status": "OK"})
    else:
        return jsonify({"status": "OK"})


class Client(object):
    def __init__(self):
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
	self.channel = self.connection.channel()

	result = self.channel.queue_declare(exclusive=True)
	self.callback_queue = result.method.queue
	self.channel.basic_consume(self.on_response, queue=self.callback_queue)

    
	result = self.channel.queue_declare(exclusive=True)
        queue_name = result.method.queue

        self.channel.basic_consume(self.on_response, queue=queue_name)
    

    def on_response(self, ch, method, props, body):
	self.response = body.decode()
	self.channel.stop_consuming()


    def call(self, keys):
	self.response = None
	self.channel.exchange_declare(exchange='hw3', exchange_type='direct')

	for key in keys:
	    self.channel.queue_bind(exchange='hw3', queue=self.callback_queue, routing_key=key)
	
	while self.response is None:
	    self.channel.start_consuming()
	
	self.connection.close()

	return self.response


@app.route("/listen", methods=['GET', 'POST'])
def listen():
    if request.method == 'POST':
        data = request.get_json()

	keys = data['keys']
   
        client = Client()
        response = client.call(keys)

        return jsonify({"msg": response})
    else:
	return jsonify({"status": "OK"})

if __name__ == "__main__":
    app.run(host='0.0.0.0')
