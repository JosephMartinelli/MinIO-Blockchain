from copy import deepcopy

import pandas as pd

from blockchain.block import Block
from blockchain.blockchain import BlockChain
from .ac_transaction import ACPolicy
from blockchain.ac_block import ACBlock, ACBlockBody
from datetime import datetime
import hashlib
from .errors import (
    NoTransactionsFound,
    ContractNotFound,
    InvalidChain,
)
from .smart_contract import SmartContract
from typing import Callable


class ACBlockchain(BlockChain):
    def __init__(
        self,
        difficulty: int,
        genesis_block: ACBlock = None,
        transactions: list[ACPolicy] = None,
    ):
        super().__init__(difficulty, genesis_block)
        if transactions:
            self.unconfirmed_transactions = transactions
        else:
            self.unconfirmed_transactions: list[ACPolicy] = []

    def create_genesis_block(self):
        block_to_add = ACBlock(index=0, timestamp=datetime.now(), previous_hash="0")
        self.proof_of_work(block_to_add)
        self.chain.append(block_to_add)

    @property
    def get_last_bloc(self) -> ACBlock:
        return self.chain[-1]

    @staticmethod
    def digest_proof_and_transactions(
        previous_proof: int,
        next_proof: int,
        index: int,
        block_body: ACBlockBody,
    ) -> bytes:
        """
        This function ties together two blocks by digesting the previous block's proof with the one
        of the current one, united with his data
        :param previous_proof: The proof of the previous block
        :param next_proof: The proof of the current block
        :param index: The current index
        :param block_body: The body of the block which contains the headers data
        :return:
        """
        math_proof = str(previous_proof**2 - next_proof**2 + index).encode()
        return math_proof + str(block_body).encode()

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
                block_body=block_to_calculate_proof.body,
            )
            computed_hash = hashlib.sha256(digested_data).hexdigest()
            if computed_hash.startswith("0" * self.difficulty):
                break
            block_to_calculate_proof.proof += 1

    def add_new_transaction(self, data: list[ACPolicy]):
        self.unconfirmed_transactions += data

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

        # Find MAC Address
        MAC = self.find_contract("MAC")
        # We temporally create a new block
        to_add = ACBlock(
            index=self.get_last_bloc.index + 1,
            timestamp=datetime.now(),
            previous_hash=self.get_last_bloc.compute_hash(),
            contract_header=deepcopy(self.get_last_bloc.body.contract_header),
            identity=deepcopy(self.get_last_bloc.body.identity),
            events=deepcopy(self.get_last_bloc.body.events),
        )
        try:
            # For each transaction call the MAC and execute it
            for transaction in self.unconfirmed_transactions:
                MAC(transaction.model_dump(), to_add)
        except Exception:
            del to_add
            raise InvalidChain("Could not mine block due to a contract error")

        self.proof_of_work(to_add)
        self.chain.append(to_add)
        self.unconfirmed_transactions = []
        return f"Block #{self.get_last_bloc.index} has been mined!"

    def is_chain_valid(self) -> bool:
        pass

    @staticmethod
    def is_block_valid(
        last_block: Block, new_block: Block, chain_difficulty: int
    ) -> bool:
        pass

    def find_contract(
        self, contract_name: str
    ) -> Callable[[dict, ACBlock], bool | str | tuple]:
        df: pd.DataFrame = self.get_last_bloc.body.contract_header
        to_return: pd.DataFrame = df.loc[df["contract_name"] == contract_name]
        if to_return.empty:
            raise ContractNotFound(
                f"No contract with name {contract_name} has been found"
            )
        else:
            return SmartContract.decode(to_return["contract_bytecode"].values[0])

    def create_blockchain_from_request(self, data: list[dict]) -> bool:
        pass

    def add_block(self, new_block: ACBlock) -> bool:
        pass

    @staticmethod
    def apply_policy_delta(
        block_policies: dict[str, ACPolicy], mem_policies: dict[str, ACPolicy]
    ):
        for block_policy_id, block_policy in block_policies.items():
            if block_policy.action == "add":
                mem_policies.update({block_policy_id: block_policy})
            elif block_policy.action == "remove":
                mem_policies.pop(block_policy_id)
            elif block_policy.action == "update":
                # This is the case that some statements have been removed/added/updated
                for (
                    block_statement_sid,
                    block_statement,
                ) in block_policy.statements.items():
                    # This is the case that the statements didn't exist so it has been added
                    if (
                        mem_policies[block_policy_id].statements.get(
                            block_statement_sid, None
                        )
                        is None
                    ):
                        mem_policies[block_policy_id].statements.update(
                            {block_statement_sid: block_statement}
                        )
                    # This is the case that the statement needs to be updated. so we need to judge the action
                    else:
                        if isinstance(block_statement.action, list):
                            action = (
                                block_statement.action[0]
                                if block_statement.action
                                else None
                            )
                        elif isinstance(block_statement.action, str):
                            action = block_statement.action
                        else:
                            action = None
                        if action != "remove":
                            mem_policies[block_policy_id].statements[
                                block_statement_sid
                            ] = block_statement
                        else:
                            del mem_policies[block_policy_id].statements[
                                block_statement_sid
                            ]
