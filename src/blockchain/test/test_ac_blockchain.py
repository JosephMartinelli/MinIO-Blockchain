import datetime
import random
from typing import Callable

import pytest

from ..ac_blockchain import ACBlockchain
from ..ac_block import ACBlock
from ..errors import ContractNotFound, InvalidChain
import pandas as pd
from copy import deepcopy

from ..smart_contract import SmartContract
from ..ac_transaction import ACPolicy, Statement

blockchain = ACBlockchain(difficulty=3)
mock_statements = {
    f"{i}": Statement(
        version="A version", sid=f"{i}", effect="Allow", resource="A resource"
    )
    for i in range(10)
}

mock_contract_header: pd.DataFrame = pd.DataFrame(
    {
        "timestamp": ["a timestamp" for i in range(10)],
        "contract_name": ["a contract_name" for i in range(10)],
        "contract_address": ["an address" for i in range(10)],
        "contract_description": ["a description" for i in range(10)],
        "contract_bytecode": [b"a bytecode" for i in range(10)],
    }
)

mock_events: pd.DataFrame = pd.DataFrame(
    {
        "timestamp": ["a timestamp" for i in range(10)],
        "requester_id": ["a requester id" for i in range(10)],
        "requester_pk": ["a requester pk" for i in range(10)],
        "transaction_type": ["a type" for i in range(10)],
    }
)

mock_identity: pd.DataFrame = pd.DataFrame(
    data={
        "timestamp": ["a timestamp" for i in range(10)],
        "ip": ["an ip" for i in range(10)],
        "pk": ["a pk" for i in range(10)],
        "role": ["a role" for i in range(10)],
        "nonce": ["a nonce" for i in range(10)],
    }
)


@pytest.fixture
def statements():
    return deepcopy(mock_statements)


@pytest.fixture
def policy(statements):
    return ACPolicy(id="An id", action="add", statements=statements)


@pytest.fixture
def headers():
    return (
        deepcopy(mock_contract_header),
        deepcopy(mock_events),
        deepcopy(mock_identity),
    )


def append_to_contract_header(df: pd.DataFrame, func: Callable) -> pd.DataFrame:
    to_append = pd.Series(
        [
            "a timestamp",
            func.__name__,
            SmartContract.create_address(SmartContract.encode(func)),
            "a description",
            SmartContract.encode(func),
        ],
        index=list(df),
    )
    return pd.concat([df, to_append.to_frame().T], ignore_index=True)


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
        1, genesis.proof, genesis.index, genesis.body
    )


def test_proof_of_work_no_data():
    block = ACBlock(
        index=50,
        timestamp="10",
        previous_hash="100",
    )
    blockchain.proof_of_work(block)
    assert block.proof != 0


def test_digest_proof_with_dataframes(policy, headers):
    contract, events, identity = headers
    block = ACBlock(
        index=50,
        timestamp="10",
        previous_hash="100",
        policies=[policy],
        contract_header=contract,
        events=events,
        identity=identity,
    )
    assert ACBlockchain.digest_proof_and_transactions(
        1, block.proof, block.proof, block.body
    )


def test_mine_no_mac(policy):
    global blockchain
    blockchain.add_new_transaction([policy])
    with pytest.raises(ContractNotFound):
        blockchain.mine()


def test_mine_with_mac_contract_error(policy, headers):
    def MAC(data: dict, block: ACBlock) -> tuple:
        print(data, block)
        raise ArithmeticError

    contract, events, identity = headers
    contract = append_to_contract_header(contract, MAC)
    # Creating a genesis block and adding it
    genesis = ACBlock(
        index=0,
        previous_hash="0",
        timestamp=datetime.datetime.now(),
        contract_header=contract,
        events=events,
        identity=identity,
    )
    local_chain = ACBlockchain(difficulty=2, genesis_block=genesis)
    local_chain.add_new_transaction([policy])
    with pytest.raises(InvalidChain):
        local_chain.mine()


def test_mine_mac_log_effect(headers, policy):
    def MAC(data: dict, block: ACBlock) -> None:
        import pandas as pd
        import datetime

        block.body.events = pd.concat(
            [
                block.body.events,
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

    contract, events, identity = headers
    contract = append_to_contract_header(contract, MAC)
    # Creating a genesis block and adding it
    genesis = ACBlock(
        index=0,
        previous_hash="0",
        timestamp=datetime.datetime.now(),
        contract_header=contract,
        events=events,
        identity=identity,
    )
    local_chain = ACBlockchain(difficulty=2, genesis_block=genesis)
    local_chain.add_new_transaction([policy])
    last_block = local_chain.get_last_bloc
    assert local_chain.mine()
    # Now we check if the events table has been modified and the block has been added
    assert last_block != local_chain.get_last_bloc, print(
        "\n", last_block, "\n", blockchain.get_last_bloc
    )
    df = local_chain.get_last_bloc.body.events
    assert not df.loc[df["transaction_type"] == "AUTHENTICATION"].empty


def test_mac_calling_other_contracts(headers, policy):
    def MAC(data: dict, block: ACBlock):
        import pandas as pd

        # Fetch PDC
        result: pd.DataFrame = block.body.contract_header.loc[
            block.body.contract_header["contract_name"] == "PDC"
        ]
        assert not result.empty
        smart_contract = SmartContract.decode(result["contract_bytecode"].values[0])
        # Execute PDC
        assert smart_contract(data, block)
        return True

    def PDC(data: dict, block: ACBlock):
        return True

    contract, events, identity = headers
    contract = append_to_contract_header(contract, MAC)
    contract = append_to_contract_header(contract, PDC)
    # Creating a genesis block and adding it
    genesis = ACBlock(
        index=0,
        previous_hash="0",
        timestamp=datetime.datetime.now(),
        contract_header=contract,
        events=events,
        identity=identity,
    )
    local_chain = ACBlockchain(difficulty=2, genesis_block=genesis)
    local_chain.add_new_transaction([policy])
    assert local_chain.mine()


def test_mac_calling_other_contracts_error(headers, policy):
    def MAC(data: dict, block: ACBlock):
        import pandas as pd

        # Fetch PDC
        result: pd.DataFrame = block.body.contract_header.loc[
            block.body.contract_header["contract_name"] == "PDC"
        ]
        assert not result.empty
        smart_contract = SmartContract.decode(result["contract_bytecode"].values[0])
        # Execute PDC
        assert smart_contract(data, block)
        return True

    def PDC(data: dict, block: ACBlock):
        return False

    contract, events, identity = headers
    contract = append_to_contract_header(contract, MAC)
    contract = append_to_contract_header(contract, PDC)
    # Creating a genesis block and adding it
    genesis = ACBlock(
        index=0,
        previous_hash="0",
        timestamp=datetime.datetime.now(),
        contract_header=contract,
        events=events,
        identity=identity,
    )
    local_chain = ACBlockchain(difficulty=2, genesis_block=genesis)
    local_chain.add_new_transaction([policy])
    with pytest.raises(InvalidChain):
        local_chain.mine()


def test_mac_calling_other_contracts_headers_can_be_modified(headers, policy):
    def MAC(data: dict, block: ACBlock):
        import pandas as pd

        # Fetch PDC
        result: pd.DataFrame = block.body.contract_header.loc[
            block.body.contract_header["contract_name"] == "PDC"
        ]
        assert not result.empty
        smart_contract = SmartContract.decode(result["contract_bytecode"].values[0])
        # Execute PDC
        assert smart_contract(data, block)
        return True

    def PDC(data: dict, block: ACBlock):
        import pandas as pd
        import datetime

        block.body.events = pd.concat(
            [
                block.body.events,
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

    contract, events, identity = headers
    contract = append_to_contract_header(contract, MAC)
    contract = append_to_contract_header(contract, PDC)
    # Creating a genesis block and adding it
    genesis = ACBlock(
        index=0,
        previous_hash="0",
        timestamp=datetime.datetime.now(),
        contract_header=contract,
        events=events,
        identity=identity,
    )
    local_chain = ACBlockchain(difficulty=2, genesis_block=genesis)
    local_chain.add_new_transaction([policy])
    assert local_chain.mine()
    df = local_chain.get_last_bloc.body.events
    assert not df.loc[df["transaction_type"] == "AUTHORIZATION"].empty


def test_policy_add(policy):
    mem_policies = {}
    blockchain.apply_policy_delta(
        block_policies={policy.id: policy}, mem_policies=mem_policies
    )
    assert mem_policies[policy.id]


def test_policy_remove(policy):
    mem_policies = {}
    blockchain.apply_policy_delta(
        block_policies={policy.id: policy}, mem_policies=mem_policies
    )
    blockchain.apply_policy_delta(
        block_policies={"Another id": policy}, mem_policies=mem_policies
    )
    policy.action = "remove"
    blockchain.apply_policy_delta(
        block_policies={policy.id: policy}, mem_policies=mem_policies
    )
    assert mem_policies.get(policy.id) is None


def test_policy_update_remove_statement(statements, policy):
    mem_policies = {}
    blockchain.apply_policy_delta(
        block_policies={policy.id: policy}, mem_policies=mem_policies
    )
    to_remove_statements = random.sample(list(statements.values()), k=4)
    for statement in to_remove_statements:
        statement.action = "remove"
    policy = ACPolicy(id=policy.id, action="update", statements=statements)
    blockchain.apply_policy_delta(
        block_policies={policy.id: policy}, mem_policies=mem_policies
    )
    for statement in to_remove_statements:
        assert mem_policies[policy.id].statements.get(statement.sid, None) is None


def test_policy_substitution_statement(statements, policy):
    mem_policies = {}
    blockchain.apply_policy_delta(
        block_policies={policy.id: policy}, mem_policies=mem_policies
    )
    to_modify_statements = random.sample(list(statements.values()), k=4)
    for statement in to_modify_statements:
        statement.effect = "Deny"
    policy = ACPolicy(id="An id", action="update", statements=statements)
    blockchain.apply_policy_delta(
        block_policies={policy.id: policy}, mem_policies=mem_policies
    )
    for statement in to_modify_statements:
        modified_statement = mem_policies[policy.id].statements.get(statement.sid, None)
        assert modified_statement
        assert modified_statement.effect == "Deny"


def test_policy_append_statements(statements, policy):
    mem_policies = {}
    blockchain.apply_policy_delta(
        block_policies={policy.id: policy}, mem_policies=mem_policies
    )
    to_append = {
        "100": Statement(
            version="A version", sid="100", effect="Deny", resource="A resource"
        )
    }
    policy = ACPolicy(id="An id", action="update", statements=to_append)
    blockchain.apply_policy_delta(
        block_policies={policy.id: policy}, mem_policies=mem_policies
    )
    retrieved_statement = mem_policies[policy.id].statements.get("100", None)
    assert retrieved_statement
    assert retrieved_statement.effect == "Deny"
