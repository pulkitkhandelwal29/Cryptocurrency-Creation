import datetime
import hashlib
import json
from flask import Flask, jsonify, request
import requests
from uuid import uuid4
from urllib.parse import urlparse

# Building a blockchain

class Blockchain:
    
    def __init__(self):
        #empty list that will contain blocks
        self.chain = []
        
        #empty list that will contain transactions
        self.transactions=[]
        
        #genesis block - first block of blockchain
        #'0' in single quote as SHA-256 accepts only encoded strings
        self.create_block(proof = 1, previous_hash = '0')
        
        #nodes will be set
        self.nodes = set()
        
    
    #this will create block once it is mined
    def create_block(self, proof, previous_hash):
        ''' Creating block with all the things required in block'''
        
        block = { 'index' : len(self.chain)+1 ,
                  'timestamp' : str(datetime.datetime.now()),
                  'proof' : proof,
                  'previous_hash' : previous_hash,
                  'transactions' : self.transactions
                 }
        
        #once transactions are appended, transaction list will again come back to empty
        self.transactions=[]
        
        #adding block in the chain of blocks
        self.chain.append(block)
        return block
    
    
    def get_previous_block(self):
        '''Return the last block of the chain'''
        return self.chain[-1]
    
    
    def proof_of_work(self,previous_proof):
        '''check the proof of work, to add the block into the blockchain'''
        new_proof = 1
        check_proof = False
        while check_proof is False:
            #This is the complex operation equation that miners will solve
            #Equation should be encoded in strings as the requirement of SHA256 and return the hexadecimal form from SHA object
            hash_operation = hashlib.sha256(str(new_proof ** 2 - previous_proof ** 2).encode()).hexdigest()
            
            #if the hash_operation has starting 4 zeros then miner won
            if hash_operation[:4] == '0000':
                check_proof = True
            else:
                new_proof += 1 #Go with the next value to try for the solving of equation
        return new_proof
    
    
    def hash(self,block):
        '''Returns the SHA256 HASH'''
        #json we have used as our block is in dictionary form
        encoded_block = json.dumps(block,sort_keys=True).encode()
        return hashlib.sha256(encoded_block).hexdigest()
    
    
    def is_chain_valid(self,chain):
        '''Checking whether the chain is valid or not'''
        previous_block = chain[0]
        block_index = 1
        while block_index < len(chain):
            block = chain[block_index]
            #if the previous hash value of block is not equal to the hash of previous block
            if block['previous_hash'] != self.hash(previous_block):
                return False
            previous_proof = previous_block['proof']
            proof = block['proof']
            hash_operation = hashlib.sha256(str(proof ** 2 - previous_proof ** 2).encode()).hexdigest()
            if hash_operation[:4] != '0000':
                return False
            previous_block = block
            block_index += 1
        return True
    
    
    def add_transaction(self,sender,receiver,amount):
        '''This will help in adding transactions'''
        self.transactions.append({
            'sender' : sender,
            'receiver' : receiver,
            'amount' : amount         
            })
        
        #this transaction must be added to next block, so getting previous block index
        previous_block = self.get_previous_block()
        return previous_block['index'] + 1
    
    
    def add_node(self,address):
        '''method that helps to add node'''
        parsed_url = urlparse(address)
        
        #after parsing the url, .netloc will give you the ip address
        self.nodes.add(parsed_url.netloc)
        
        
    def replace_chain(self):
        #containing all nodes
        network = self.nodes
        
        longest_chain = None
        
        #length of the longest chain
        max_length = len(self.chain)
        
        for node in network:
            #get 127.0.0.1:5000,5001 (all nodes)
            response = requests.get(f'http://(node)/get_chain')
            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']
                
                #assigning the longest chain from the longest length
                if length > max_length and self.is_chain_valid(chain):
                    max_length = length
                    longest_chain = chain
            
        if longest_chain:
            #if longest chain is not None, then we will replace chain and return True
            self.chain = longest_chain
            return True
        return False
    
    
# Mining our Blockchain


## Create a web app
app = Flask(__name__)


#Creating an address for the node on Port 5000
node_address = str(uuid4()).replace('=','')

## Create a blockchain
blockchain = Blockchain()

## Mining a new block
@app.route('/mine_block', methods = ['GET'])
def mine_block():
    #return previous block
    previous_block = blockchain.get_previous_block()
    #returns previous proof of block
    previous_proof = previous_block['proof']
    proof = blockchain.proof_of_work(previous_proof)
    
    #get previous hash
    previous_hash = blockchain.hash(previous_block)
    
    blockchain.add_transaction(sender = node_address, receiver = 'Pulkit', amount = 1)
    
    #create block function invoked
    block = blockchain.create_block(proof, previous_hash)
    
    response = {'message' : 'Congratulations, you just mined a block!',
                'index' : block['index'],
                'timestamp' : block['timestamp'],
                'proof' : block['proof'],
                'previous_hash' : block['previous_hash'],
                'transactions': block['transactions']
                }
    return jsonify(response), 200 #for the HTTP status code


## Getting the full Blockchain
@app.route('/get_chain', methods = ['GET'])
def get_chain():
    response = {'chain' : blockchain.chain,
                'length' : len(blockchain.chain)               
                }
    return jsonify(response), 200


## Check the blockchain is valid or not
@app.route('/is_valid', methods = ['GET'])
def is_valid():
    is_valid = blockchain.is_chain_valid(blockchain.chain)
    if is_valid:
        response = {'message' : 'Blockchain is valid !'}
    else:
        response = {'message' : 'Houston, we have a problem. Blockchain is not valid '}
    
    return jsonify(response), 200


# Adding a new transaction to the blockchain
@app.route('/add_transaction', methods = ['POST'])
def add_transaction():
    #get json file posted in postman
    json = request.get_json()
    #3 keys of transaction
    transaction_keys = ['sender','receiver','amount']

    if not all (key in json for keys in transaction_keys):
        return 'Some elements of the transaction are missing',400 #400 is for Bad Request code
    
    index = blockchain.add_transaction(json['sender'],json['receiver'],json['amount'])
    
    response = {'message': f'This transaction will be added to Block {index}'}
    
    return jsonify(response), 201


## Running the app
app.run(port = 5000)
















    
    
    
    