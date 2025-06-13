import datetime

import pytest

from ..ac_blockchain import ACBlockchain
from ..ac_block import ACBlock
from ..errors import ContractNotFound, InvalidChain
import pandas as pd
from copy import deepcopy
from pydantic import ValidationError
from datetime import date


from ..smart_contract import SmartContract

blockchain = ACBlockchain(difficulty=3)
transaction = {
    "contract_address": "",
    "data": ["test"],
    "timestamp": datetime.date.today(),
    "requester_id": "",
    "requester_pk": "",
    "transaction_type": "AUTHORIZATION",
}
mock_contract_data = {
    "timestamp": [],
    "contract_name": [],
    "contract_address": [],
    "contract_description": [],
    "contract_bytecode": [],
}


## Cleanup function
@pytest.fixture(autouse=True)
def cleanup():
    global blockchain
    yield
    blockchain.unconfirmed_transactions = []
    del blockchain.chain[1:]


def test_genesis_block_creation():
    assert len(blockchain.chain) > 0


def test_create_passed_genesis_block():
    genesis = ACBlock(
        index=50,
        timestamp="10",
        previous_hash="100",
    )
    local_chain = ACBlockchain(difficulty=3, genesis_block=genesis)
    assert len(local_chain.chain) == 1
    assert local_chain.chain[-1] == genesis
    assert local_chain.chain[-1].proof != 0


def test_digest_proof_and_no_dataframes():
    genesis = ACBlock(index=0, timestamp="10", previous_hash="100", proof=100)
    assert ACBlockchain.digest_proof_and_transactions(
        1, genesis.proof, genesis.index, genesis.get_headers
    )


def test_proof_of_work_no_dataframes():
    block = ACBlock(
        index=50,
        timestamp="10",
        previous_hash="100",
    )
    blockchain.proof_of_work(block)
    assert block.proof != 0


def test_digest_proof_with_dataframes():
    policy_header = pd.DataFrame(
        {
            "requester_id": ["1", "100", "1000"],
            "requester_group": ["user", "user", "user"],
            "action": ["s3:getBucket", "s3:getBucket", "s3:getBucket"],
            "resource": ["test", "test", "test"],
            "allowed": [False, False, False],
        }
    )
    block = ACBlock(
        index=50, timestamp="10", previous_hash="100", policy_heder=policy_header
    )
    assert ACBlockchain.digest_proof_and_transactions(
        1, block.proof, block.proof, block.get_headers
    )


def test_mine_invalid_transactions():
    global blockchain, transaction
    local_tr = deepcopy(transaction)
    local_tr["transaction_type"] = "10"
    with pytest.raises(ValidationError):
        blockchain.add_new_transaction([local_tr])


def test_mine_no_mac():
    global blockchain, transaction
    local_tr = deepcopy(transaction)
    local_tr["transaction_type"] = "ADD_CONTRACT"
    local_tr["timestamp"] = date.today()
    blockchain.add_new_transaction([local_tr])
    with pytest.raises(ContractNotFound):
        blockchain.mine()


def test_mine_with_mac_contract_error():
    def MAC(data: dict, context: list[pd.DataFrame]) -> tuple:
        print(data, context)
        raise ArithmeticError

    global mock_contract_data, transaction
    local_contrat = deepcopy(mock_contract_data)
    local_contrat["timestamp"].append(datetime.date.today())
    local_contrat["contract_name"].append("MAC")
    local_contrat["contract_description"].append("")
    local_contrat["contract_bytecode"].append(SmartContract.encode(MAC))
    local_contrat["contract_address"].append(
        SmartContract.create_address(SmartContract.encode(MAC))
    )
    # Creating a genesis block and adding it
    genesis = ACBlock(
        index=0,
        previous_hash="0",
        timestamp=datetime.datetime.now(),
        contract_header=pd.DataFrame(local_contrat),
    )
    local_chain = ACBlockchain(difficulty=2, genesis_block=genesis)
    local_chain.add_new_transaction([deepcopy(transaction)])
    with pytest.raises(InvalidChain):
        local_chain.mine()


def test_mine_mac_log_effect():
    def MAC(data: dict, block: ACBlock) -> tuple:
        import pandas as pd
        import datetime

        block.events = pd.concat(
            [
                block.events,
                pd.DataFrame(
                    [
                        [
                            datetime.date.today(),
                            "An id",
                            "A key",
                            "AUTHENTICATION",
                        ]
                    ],
                    columns=[
                        "timestamp",
                        "requester_id",
                        "requester_pk",
                        "transaction_type",
                    ],
                ),
            ],
            ignore_index=True,
        )

    global mock_contract_data, transaction
    local_contrat = deepcopy(mock_contract_data)
    local_contrat["timestamp"].append(datetime.date.today())
    local_contrat["contract_name"].append("MAC")
    local_contrat["contract_description"].append("")
    local_contrat["contract_bytecode"].append(SmartContract.encode(MAC))
    local_contrat["contract_address"].append(
        SmartContract.create_address(SmartContract.encode(MAC))
    )
    # Creating a genesis block and adding it
    genesis = ACBlock(
        index=0,
        previous_hash="0",
        timestamp=datetime.datetime.now(),
        contract_header=pd.DataFrame(local_contrat),
    )
    local_chain = ACBlockchain(difficulty=2, genesis_block=genesis)
    local_chain.add_new_transaction([deepcopy(transaction)])
    local_chain.mine()
    assert not local_chain.get_last_bloc.events.empty


def test_mac_calling_other_contracts():
    def MAC(data: dict, block: ACBlock):
        import pandas as pd

        if data["transaction_type"] == "AUTHORIZATION":
            # Fetch PDC
            result: pd.DataFrame = block.contract_header.loc[
                block.contract_header["contract_name"] == "PDC"
            ]
            assert not result.empty
            smart_contract = SmartContract.decode(result["contract_bytecode"].values[0])
            # Execute PDC
            assert smart_contract(data, block)
        return True

    def PDC(data: dict, block: ACBlock):
        return True

    global mock_contract_data, transaction
    local_contrat = deepcopy(mock_contract_data)
    local_contrat["timestamp"].append(datetime.date.today())
    local_contrat["contract_name"].append("MAC")
    local_contrat["contract_description"].append("")
    local_contrat["contract_bytecode"].append(SmartContract.encode(MAC))
    local_contrat["contract_address"].append(
        SmartContract.create_address(SmartContract.encode(MAC))
    )
    local_contrat["timestamp"].append(datetime.date.today())
    local_contrat["contract_name"].append("PDC")
    local_contrat["contract_description"].append("")
    local_contrat["contract_bytecode"].append(SmartContract.encode(PDC))
    local_contrat["contract_address"].append(
        SmartContract.create_address(SmartContract.encode(PDC))
    )
    # Creating a genesis block and adding it
    genesis = ACBlock(
        index=0,
        previous_hash="0",
        timestamp=datetime.datetime.now(),
        contract_header=pd.DataFrame(local_contrat),
    )
    local_chain = ACBlockchain(difficulty=2, genesis_block=genesis)
    local_chain.add_new_transaction([deepcopy(transaction)])
    assert local_chain.mine()


def test_mac_calling_other_contracts_headers_can_be_modified():
    def MAC(data: dict, block: ACBlock):
        import pandas as pd

        if data["transaction_type"] == "AUTHORIZATION":
            # Fetch PDC
            result: pd.DataFrame = block.contract_header.loc[
                block.contract_header["contract_name"] == "PDC"
            ]
            assert not result.empty
            smart_contract = SmartContract.decode(result["contract_bytecode"].values[0])
            # Execute PDC
            assert smart_contract(data, block)
        return True

    def PDC(data: dict, block: ACBlock):
        import pandas as pd
        import datetime

        block.events = pd.concat(
            [
                block.events,
                pd.DataFrame(
                    [
                        [
                            datetime.date.today(),
                            "An id",
                            "A key",
                            "AUTHORIZATION",
                        ]
                    ],
                    columns=[
                        "timestamp",
                        "requester_id",
                        "requester_pk",
                        "transaction_type",
                    ],
                ),
            ],
            ignore_index=True,
        )

    return True

    global mock_contract_data, transaction
    local_contrat = deepcopy(mock_contract_data)
    local_contrat["timestamp"].append(datetime.date.today())
    local_contrat["contract_name"].append("MAC")
    local_contrat["contract_description"].append("")
    local_contrat["contract_bytecode"].append(SmartContract.encode(MAC))
    local_contrat["contract_address"].append(
        SmartContract.create_address(SmartContract.encode(MAC))
    )
    local_contrat["timestamp"].append(datetime.date.today())
    local_contrat["contract_name"].append("PDC")
    local_contrat["contract_description"].append("")
    local_contrat["contract_bytecode"].append(SmartContract.encode(PDC))
    local_contrat["contract_address"].append(
        SmartContract.create_address(SmartContract.encode(PDC))
    )
    # Creating a genesis block and adding it
    genesis = ACBlock(
        index=0,
        previous_hash="0",
        timestamp=datetime.datetime.now(),
        contract_header=pd.DataFrame(local_contrat),
    )
    local_chain = ACBlockchain(difficulty=2, genesis_block=genesis)
    local_chain.add_new_transaction([deepcopy(transaction)])
    assert local_chain.mine()
    assert not local_chain.get_last_bloc.contract_header.empty
