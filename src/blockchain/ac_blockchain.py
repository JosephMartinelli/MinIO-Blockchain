from copy import deepcopy

import pandas as pd

from blockchain.block import Block
from blockchain.blockchain import BlockChain
from .transaction import ACTransaction
from blockchain.ac_block import ACBlock
from datetime import datetime
import hashlib
from .errors import (
    NoTransactionsFound,
    ContractNotFound,
    InvalidChain,
    ContractError,
)
from .smart_contract import SmartContract


class ACBlockchain(BlockChain):
    def __init__(
        self,
        difficulty: int,
        genesis_block: ACBlock = None,
        transactions: list[ACTransaction] = None,
    ):
        super().__init__(difficulty, genesis_block)
        if transactions:
            self.unconfirmed_transactions = [tr.model_dump() for tr in transactions]
        else:
            self.unconfirmed_transactions: list[ACTransaction] = []

    def create_genesis_block(self):
        block_to_add = ACBlock(index=0, timestamp=datetime.now(), previous_hash="0")
        self.proof_of_work(block_to_add)
        self.chain.append(block_to_add)

    @property
    def get_last_bloc(self) -> ACBlock:
        return self.chain[-1]

    @staticmethod
    def digest_proof_and_transactions(
        previous_proof: int, next_proof: int, index: int, headers: list[pd.DataFrame]
    ) -> bytes:
        """
        This function ties together two blocks by digesting the previous block's proof with the one
        of the current one, united with his data
        :param previous_proof: The proof of the previous block
        :param next_proof: The proof of the current block
        :param index: The current index
        :param headers: The headers of a block
        :return:
        """
        math_proof = str(previous_proof**2 - next_proof**2 + index).encode()
        return math_proof + "".join([header.to_json() for header in headers]).encode()

    def proof_of_work(self, block_to_calculate_proof: ACBlock) -> None:
        """
        This function tries different values of the proof and finds a suitable value that satisfies the difficulty
        set by the blockchain. The nonce is then stored in the block
        :return:
        """
        current_index = len(self.chain)
        if current_index == 0:
            previous_proof = 0
        else:
            previous_proof = self.get_last_bloc.proof
        while True:
            digested_data = ACBlockchain.digest_proof_and_transactions(
                previous_proof=previous_proof,
                next_proof=block_to_calculate_proof.proof,
                index=current_index,
                headers=block_to_calculate_proof.get_headers,
            )
            computed_hash = hashlib.sha256(digested_data).hexdigest()
            if computed_hash.startswith("0" * self.difficulty):
                break
            block_to_calculate_proof.proof += 1

    def add_new_transaction(self, data: list[dict[str, ...]]):
        self.unconfirmed_transactions += [ACTransaction(**x) for x in data]

    def mine(self) -> str:
        """
        This function adds pending transactions to a block and figures
        out the proof of work.
        For the time being we do not allow contracts to call other contracts
        :return:
        """
        # This is the case no transaction is available
        if not self.unconfirmed_transactions:
            raise NoTransactionsFound("No unconfirmed transactions have been found!")

        # Find MAC Address
        contract_info = self.find_contract("MAC")
        if contract_info.empty:
            raise ContractNotFound("Could not find MAC")
        # We temporally add a new block to the chain so
        # that any smart contract could modify it
        # In case of errors we revert back
        self.chain.append(deepcopy(self.get_last_bloc))
        try:
            # For each transaction call the MAC and execute it
            for transaction in self.unconfirmed_transactions:
                smart_contract = SmartContract.decode(
                    contract_info[0, "contrat_bytecode"]
                )
                smart_contract(transaction.model_dump(), self.get_last_bloc.get_headers)
        except ContractError:
            self.chain.pop(-1)
            raise InvalidChain("Could not mine block due to a contract error")

        self.proof_of_work(self.get_last_bloc)
        self.unconfirmed_transactions = []
        return f"Block #{self.get_last_bloc.index} has been mined!"

    def is_chain_valid(self) -> bool:
        pass

    @staticmethod
    def is_block_valid(
        last_block: Block, new_block: Block, chain_difficulty: int
    ) -> bool:
        pass

    def find_contract(self, contract_name: str) -> pd.DataFrame:
        df: pd.DataFrame = self.get_last_bloc.contract_header
        return df.loc[df["contract_name"] == contract_name]

    def create_blockchain_from_request(self, data: list[dict]) -> bool:
        pass
