"""Much of the code has been taken from this wonderful tutorial
https://gist.github.com/satwikkansal/4a857cad2797b9d199547a752933a715
and the following video
https://www.bing.com/videos/riverview/relatedvideo?q=python+api+for+blockchain&mid=7ABED193A02AE8493E617ABED193A02AE8493E61&FORM=VIRE
"""

from .block import Block
from abc import ABC, abstractmethod


class BlockChain(ABC):
    def __init__(self, difficulty: int, genesis_block: Block = None):
        self.chain: list[Block] = []
        if genesis_block:
            self.chain.append(genesis_block)
        else:
            self.create_genesis_block()
        self.difficulty = difficulty  # This is the difficulty of the PoW algorithm into the calculating the nonce

    @abstractmethod
    def create_genesis_block(self):
        pass

    @staticmethod
    @abstractmethod
    def digest_proof_and_transactions(
        previous_proof: int,
        next_proof: int,
        index: int,
        transactions: list[dict],
    ) -> bytes:
        pass

    @abstractmethod
    def proof_of_work(self, block_to_calculate_proof: Block) -> None:
        """
        This function tries different values of the proof and finds a suitable value that satisfies the difficulty
        set by the blockchain. The nonce is then stored in the block
        :return:
        """
        pass

    @abstractmethod
    def add_new_transaction(self, data: list[dict[str, ...]]):
        """
        This function checks if the transactions are in the format {'data':...,'is_contract':...,'contract_address':...
        } and if so it adds them to the pool of unconfirmed transactions}
        :param data:
        :return:
        """
        pass

    @abstractmethod
    def mine(self) -> str:
        """
        This function adds pending transactions to a block and figures
        out the proof of work.
        For the time being we do not allow contracts to call other contracts
        :return:
        """
        pass

    @property
    def get_last_bloc(self) -> Block:
        return self.chain[-1]

    @abstractmethod
    def is_chain_valid(self) -> bool:
        """
        This function checks each block's hash of the chain with the field 'previous_hash' of the block immediately next
        to it. If there is a mismatch, then it means that the transactions have been altered and the chain is no longer
        valid.
        :return:
        """
        pass

    @staticmethod
    @abstractmethod
    def is_block_valid(
        last_block: Block, new_block: Block, chain_difficulty: int
    ) -> bool:
        pass

    @abstractmethod
    def find_contract(self, contract_address: str) -> str | None:
        """
        This function given a contract address searches across all the blockchain and finds the contract's bytecode
        associated of the contract address found
        :param contract_address:
        :return:
        """
        pass

    @abstractmethod
    def create_blockchain_from_request(self, data: list[dict]) -> bool:
        """
        This function creates a new blockchain given a list of blocks. As each block is inserted, both the transactional
        data it holds and the block itself are validated.
        :param data:
        :return:
        """
        pass
