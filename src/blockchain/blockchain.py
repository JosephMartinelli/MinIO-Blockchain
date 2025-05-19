"""Much of the code has been taken from this wonderful tutorial
https://gist.github.com/satwikkansal/4a857cad2797b9d199547a752933a715
and the following video
https://www.bing.com/videos/riverview/relatedvideo?q=python+api+for+blockchain&mid=7ABED193A02AE8493E617ABED193A02AE8493E61&FORM=VIRE
"""

from datetime import datetime
import json
import hashlib

from .block import Block
from .transaction import Transaction
from .smart_contract import SmartContract
from .errors import (
    NoTransactionsFound,
    ContractNotFound,
    InvalidChain,
)


class BlockChain:
    def __init__(self, difficulty: int, genesis_block: Block = None):
        self.chain: list[Block] = []
        if genesis_block:
            self.chain.append(genesis_block)
        else:
            self.create_genesis_block()
        self.difficulty = difficulty  # This is the difficulty of the PoW algorithm into the calculating the nonce
        self.unconfirmed_transactions: list[
            Transaction
        ] = []  # Pool of transaction that need to be validated (or mined)

    def create_genesis_block(self):
        genesis_block = Block(0, datetime.now(), "0")
        genesis_block.previous_hash = 0
        self.chain.append(genesis_block)

    @staticmethod
    def digest_proof_and_transactions(
        previous_proof: int,
        next_proof: int,
        index: int,
        transactions: list[dict],
    ) -> bytes:
        math_proof = str(previous_proof**2 - next_proof**2 + index).encode()
        transaction_data = json.dumps(transactions).encode()
        return math_proof + transaction_data

    def proof_of_work(self, block_to_calculate_proof: Block):
        """
        This function tries different values of the proof and finds a suitable value that satisfies the difficulty
        set by the blockchain. The nonce is then stored in the block
        :return:
        """
        previous_proof = self.get_last_bloc.proof
        current_index = len(self.chain)
        while True:
            digested_data = BlockChain.digest_proof_and_transactions(
                previous_proof=previous_proof,
                next_proof=block_to_calculate_proof.proof,
                index=current_index,
                transactions=block_to_calculate_proof.transactions,
            )
            computed_hash = hashlib.sha256(digested_data).hexdigest()
            if computed_hash.startswith("0" * self.difficulty):
                break
            block_to_calculate_proof.proof += 1

    def add_new_transaction(self, data: list[dict[str, ...]]):
        """
        This function checks if the transactions are in the format {'data':...,'is_contract':...,'contract_address':...
        } and if so it adds them to the pool of unconfirmed transactions}
        :param data:
        :return:
        """
        print([Transaction(**x) for x in data])
        self.unconfirmed_transactions += [Transaction(**x) for x in data]

    def mine(self):
        """
        This function adds pending transactions to a block and figures
        out the proof of work.
        For the time being we do not allow contracts to call other contracts
        :return:
        """
        # This is the case no transaction is available
        if not self.unconfirmed_transactions:
            raise NoTransactionsFound("No unconfirmed transactions have been found!")

        # We check each transaction for:
        # 1. If it is a contract, then we calculate the contract address by hashing the bytecode
        # 2. Checking if the transaction refers a contract, if it is then the contract is fetched, decoded and executed
        # 3. If it refers no contract, then we do nothing
        for transaction in self.unconfirmed_transactions:
            if transaction.is_contract and not transaction.contract_address:
                transaction.contract_address = hashlib.sha256(
                    transaction.data.encode()
                ).hexdigest()
                continue
            if transaction.contract_address:
                func_bytes = self.find_contract(transaction.contract_address)
                if func_bytes is None:
                    raise ContractNotFound(
                        "No contract has been found with that address!"
                    )
                smart_contract = SmartContract.decode(func_bytes)
                # Execute it
                smart_contract(transaction.data)

        # This is the last step, where everything is encoded and add it to the blockchain
        last_hash = self.get_last_bloc.compute_hash()
        index = self.get_last_bloc.index + 1

        new_block = Block(
            index=index,
            transactions=self.unconfirmed_transactions,
            timestamp=datetime.now(),
            previous_hash=last_hash,
        )
        self.proof_of_work(new_block)
        self.chain.append(new_block)
        self.unconfirmed_transactions = []
        return f"Block #{new_block.index} has been mined!"

    @property
    def get_last_bloc(self) -> Block:
        return self.chain[-1]

    def is_chain_valid(self) -> bool:
        """
        This function checks each block's hash of the chain with the field 'previous_hash' of the block immediately next
        to it. If there is a mismatch, then it means that the transactions have been altered and the chain is no longer
        valid.
        :return:
        """
        for i in range(len(self.chain) - 1):
            current_block: Block = self.chain[i]
            next_block: Block = self.chain[i + 1]
            # This checks that the hash the block is referring to is valid
            if next_block.previous_hash != current_block.compute_hash():
                raise InvalidChain(
                    "Hash missmatch of the current block with the hash of the previous block"
                )
            # Then we check that the proof of work generated by the block respects the complexity of the blockchain
            # This is the digested data of the next block
            digested_data = self.digest_proof_and_transactions(
                next_proof=next_block.proof,
                previous_proof=current_block.proof,
                transactions=next_block.transactions,
                index=next_block.index,
            )
            block_hash = hashlib.sha256(digested_data).hexdigest()
            if not block_hash.startswith("0" * self.difficulty):
                raise InvalidChain(
                    f"Block {next_block.__dict__} has been rejected due to an hash alteration, data has been tampered!"
                )
        return True

    def add_block(self, new_block: Block) -> bool:
        last_block = self.get_last_bloc
        if new_block.index != (last_block.index + 1):
            raise IndexError(
                f"Current index is {last_block.index}, but the index passed is {new_block.index}"
            )
        if last_block.compute_hash() != new_block.previous_hash:
            raise InvalidChain(
                "The passed hash is not consistent with the hash of the last block"
            )
        digested_data = self.digest_proof_and_transactions(
            next_proof=new_block.proof,
            previous_proof=last_block.proof,
            transactions=new_block.transactions,
            index=new_block.index,
        )
        block_hash = hashlib.sha256(digested_data).hexdigest()
        if not block_hash.startswith("0" * self.difficulty):
            raise InvalidChain("Block hash is not consistent with chain difficulty")
        self.chain.append(new_block)
        return True

    def find_contract(self, contract_address: str) -> str | None:
        """
        This function given a contract address searches across all the blockchain and finds the contract's bytecode
        associated of the contract address found
        :param contract_address:
        :return:
        """
        for block in self.chain:
            if block.transactions:
                for transaction in block.transactions:
                    if (
                        transaction["is_contract"]
                        and transaction["contract_address"] == contract_address
                    ):
                        # Return the function bytecode
                        return transaction["data"]
        return None
