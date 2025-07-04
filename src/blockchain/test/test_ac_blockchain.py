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
from ..ac_transaction import (
    ACResourcePolicy,
    ACIdentityPolicy,
    ACIdentityStatement,
    ACResourceStatement,
)

from pydantic_core._pydantic_core import ValidationError

blockchain = ACBlockchain(difficulty=3)
mock_resource_statements = {
    f"{i}": ACResourceStatement(
        version="A version",
        sid=f"{i}",
        effect="Allow",
        resource="A resource",
        principal=f"principal{i}",
    )
    for i in range(10)
}

mock_contract_header: pd.DataFrame = pd.DataFrame(
    {
        "timestamp": ["a timestamp" for i in range(10)],
        "contract_name": ["a contract_name" for i in range(10)],
        "contract_address": ["an address" for i in range(10)],
        "contract_description": ["a description" for i in range(10)],
        "contract_bytecode": ["b a bytecode str" for i in range(10)],
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

mock_identity_statements = {
    f"{i}": ACIdentityStatement(
        version="A version", sid=f"{i}", effect="Allow", resource="A resource"
    )
    for i in range(10)
}


@pytest.fixture
def resource_statements():
    return deepcopy(mock_resource_statements)


@pytest.fixture
def identity_statements():
    return deepcopy(mock_identity_statements)


@pytest.fixture
def resource_policy(resource_statements):
    return ACResourcePolicy(id="An id", action="add", statements=resource_statements)


@pytest.fixture
def identity_policy(identity_statements):
    return {
        "principal_id": {
            "policy_id": ACIdentityPolicy(
                id="An id", action="add", statements=identity_statements
            )
        }
    }


@pytest.fixture
def headers():
    return (deepcopy(mock_contract_header), deepcopy(mock_events))


def random_headers(headers):
    contract, events = headers
    return (
        contract.sample(frac=0.5),
        events.sample(frac=0.5),
    )


def random_resource_statements():
    random_sts = random.sample(list(deepcopy(mock_resource_statements).values()), 5)
    return {random_st.sid: random_st for random_st in random_sts}


def random_identity_statements():
    random_sts = random.sample(list(deepcopy(mock_identity_statements).values()), 5)
    return {random_st.sid: random_st for random_st in random_sts}


def random_resource_policies():
    return [
        ACResourcePolicy(
            id=str(i), action="add", statements=random_resource_statements()
        )
        for i in range(random.randint(1, 10))
    ]


def random_identity_policies():
    return {
        "a principal id": {
            f"{i}": ACIdentityPolicy(
                id=str(i), action="add", statements=random_identity_statements()
            )
            for i in range(random.randint(1, 10))
        }
    }


@pytest.fixture
def chain_with_blocks(headers) -> ACBlockchain:
    chain = ACBlockchain(difficulty=2)
    for i in range(10):
        contract, events = random_headers(headers)
        block = ACBlock(
            index=chain.get_last_bloc.index + 1,
            timestamp=datetime.datetime.now(),
            previous_hash=chain.get_last_bloc.compute_hash(),
            resource_policies=random_resource_policies(),
            contract_header=contract,
            events=events,
            identity_policies=random_identity_policies(),
        )
        chain.proof_of_work(block)
        chain.add_block(block)
    return chain


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


def test_digest_proof_with_dataframes(resource_policy, identity_policy, headers):
    contract, events = headers
    block = ACBlock(
        index=50,
        timestamp="10",
        previous_hash="100",
        resource_policies=[resource_policy],
        contract_header=contract,
        events=events,
        identity_policies=identity_policy,
    )
    assert ACBlockchain.digest_proof_and_transactions(
        1, block.proof, block.proof, block.body
    )


def test_mine_no_mac(resource_policy):
    global blockchain
    blockchain.add_new_transaction([resource_policy])
    with pytest.raises(ContractNotFound):
        blockchain.mine()


def test_mine_with_mac_contract_error(resource_policy, identity_policy, headers):
    def MAC(data: dict, block: ACBlock) -> tuple:
        raise ArithmeticError

    contract, events = headers
    contract = append_to_contract_header(contract, MAC)
    # Creating a genesis block and adding it
    genesis = ACBlock(
        index=0,
        previous_hash="0",
        timestamp=datetime.datetime.now(),
        contract_header=contract,
        events=events,
        identity_policies=identity_policy,
    )
    local_chain = ACBlockchain(difficulty=2, genesis_block=genesis)
    local_chain.add_new_transaction([resource_policy])
    with pytest.raises(InvalidChain):
        local_chain.mine()


def test_mine_mac_log_effect(headers, resource_policy, identity_policy):
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

    contract, events = headers
    contract = append_to_contract_header(contract, MAC)
    # Creating a genesis block and adding it
    genesis = ACBlock(
        index=0,
        previous_hash="0",
        timestamp=datetime.datetime.now(),
        contract_header=contract,
        events=events,
        identity_policies=identity_policy,
    )
    local_chain = ACBlockchain(difficulty=2, genesis_block=genesis)
    local_chain.add_new_transaction([resource_policy])
    last_block = local_chain.get_last_bloc
    assert local_chain.mine()
    # Now we check if the events table has been modified and the block has been added
    assert last_block != local_chain.get_last_bloc, print(
        "\n", last_block, "\n", blockchain.get_last_bloc
    )
    df = local_chain.get_last_bloc.body.events
    assert not df.loc[df["transaction_type"] == "AUTHENTICATION"].empty


def test_mac_calling_other_contracts(headers, resource_policy, identity_policy):
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

    contract, events = headers
    contract = append_to_contract_header(contract, MAC)
    contract = append_to_contract_header(contract, PDC)
    # Creating a genesis block and adding it
    genesis = ACBlock(
        index=0,
        previous_hash="0",
        timestamp=datetime.datetime.now(),
        contract_header=contract,
        events=events,
        identity_policies=identity_policy,
    )
    local_chain = ACBlockchain(difficulty=2, genesis_block=genesis)
    local_chain.add_new_transaction([resource_policy])
    assert local_chain.mine()


def test_mac_calling_other_contracts_error(headers, resource_policy, identity_policy):
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

    contract, events = headers
    contract = append_to_contract_header(contract, MAC)
    contract = append_to_contract_header(contract, PDC)
    # Creating a genesis block and adding it
    genesis = ACBlock(
        index=0,
        previous_hash="0",
        timestamp=datetime.datetime.now(),
        contract_header=contract,
        events=events,
        identity_policies=identity_policy,
    )
    local_chain = ACBlockchain(difficulty=2, genesis_block=genesis)
    local_chain.add_new_transaction([resource_policy])
    with pytest.raises(InvalidChain):
        local_chain.mine()


def test_mac_calling_other_contracts_headers_can_be_modified(
    headers, resource_policy, identity_policy
):
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

    contract, events = headers
    contract = append_to_contract_header(contract, MAC)
    contract = append_to_contract_header(contract, PDC)
    # Creating a genesis block and adding it
    genesis = ACBlock(
        index=0,
        previous_hash="0",
        timestamp=datetime.datetime.now(),
        contract_header=contract,
        events=events,
        identity_policies=identity_policy,
    )
    local_chain = ACBlockchain(difficulty=2, genesis_block=genesis)
    local_chain.add_new_transaction([resource_policy])
    assert local_chain.mine()
    df = local_chain.get_last_bloc.body.events
    assert not df.loc[df["transaction_type"] == "AUTHORIZATION"].empty


def test_policy_add(resource_policy):
    mem_policies = {}
    blockchain.apply_resource_policy_delta(
        block_resource_policies={resource_policy.id: resource_policy},
        mem_policies=mem_policies,
    )
    assert mem_policies[resource_policy.id]


def test_policy_remove(resource_policy):
    mem_policies = {}
    blockchain.apply_resource_policy_delta(
        block_resource_policies={resource_policy.id: resource_policy},
        mem_policies=mem_policies,
    )
    blockchain.apply_resource_policy_delta(
        block_resource_policies={"Another id": resource_policy},
        mem_policies=mem_policies,
    )
    resource_policy.action = "remove"
    blockchain.apply_resource_policy_delta(
        block_resource_policies={resource_policy.id: resource_policy},
        mem_policies=mem_policies,
    )
    assert mem_policies.get(resource_policy.id) is None


def test_policy_update_remove_statement(resource_statements, resource_policy):
    mem_policies = {}
    blockchain.apply_resource_policy_delta(
        block_resource_policies={resource_policy.id: resource_policy},
        mem_policies=mem_policies,
    )
    to_remove_statements = random.sample(list(resource_statements.values()), k=4)
    for statement in to_remove_statements:
        statement.action = "remove"
    policy = ACResourcePolicy(
        id=resource_policy.id, action="update", statements=resource_statements
    )
    blockchain.apply_resource_policy_delta(
        block_resource_policies={policy.id: policy}, mem_policies=mem_policies
    )
    for statement in to_remove_statements:
        assert mem_policies[policy.id].statements.get(statement.sid, None) is None


def test_policy_substitution_statement(resource_statements, resource_policy):
    mem_policies = {}
    blockchain.apply_resource_policy_delta(
        block_resource_policies={resource_policy.id: resource_policy},
        mem_policies=mem_policies,
    )
    to_modify_statements = random.sample(list(resource_statements.values()), k=4)
    for statement in to_modify_statements:
        statement.effect = "Deny"
    policy = ACResourcePolicy(
        id="An id", action="update", statements=resource_statements
    )
    blockchain.apply_resource_policy_delta(
        block_resource_policies={policy.id: policy}, mem_policies=mem_policies
    )
    for statement in to_modify_statements:
        modified_statement = mem_policies[policy.id].statements.get(statement.sid, None)
        assert modified_statement
        assert modified_statement.effect == "Deny"


def test_policy_append_statements(resource_statements, resource_policy):
    mem_policies = {}
    blockchain.apply_resource_policy_delta(
        block_resource_policies={resource_policy.id: resource_policy},
        mem_policies=mem_policies,
    )
    to_append = {
        "100": ACResourceStatement(
            version="A version", sid="100", effect="Deny", resource="A resource"
        )
    }
    policy = ACResourcePolicy(id="An id", action="update", statements=to_append)
    blockchain.apply_resource_policy_delta(
        block_resource_policies={policy.id: policy}, mem_policies=mem_policies
    )
    retrieved_statement = mem_policies[policy.id].statements.get("100", None)
    assert retrieved_statement
    assert retrieved_statement.effect == "Deny"


def test_bad_policy_create_blockchain_from_request(
    resource_policy, headers, chain_with_blocks
):
    # We get a chain, and we convert it to a string
    str_chain: list[dict] = [block.to_dict() for block in chain_with_blocks.chain]
    assert len(str_chain) > 2
    # Modify random elem
    for block in random.sample(str_chain, k=2):
        if not list(block["body"]["resource_policies"].values()):
            continue
        r_policies: ACResourcePolicy = random.sample(
            list(block["body"]["resource_policies"].values()), 1
        )
        list(r_policies[0]["statements"].values())[0]["version"] = 10
    local_chain = ACBlockchain(difficulty=chain_with_blocks.difficulty)
    with pytest.raises(ValidationError):
        local_chain.create_blockchain_from_request(str_chain)


def test_create_blockchain_from_request(resource_policy, headers, chain_with_blocks):
    # We get a chain, and we convert it to a string
    str_chain: list[dict] = [block.to_dict() for block in chain_with_blocks.chain]
    local_chain = ACBlockchain(difficulty=chain_with_blocks.difficulty)
    assert local_chain.create_blockchain_from_request(str_chain)
    assert len(local_chain.chain) > 1
    for local_block, original_block in zip(local_chain.chain, chain_with_blocks.chain):
        assert local_block == original_block


def test_create_blockchain_from_request_can_decode_contracts(
    resource_policy, headers, chain_with_blocks, identity_policy
):
    # We get a chain, and we convert it to a string
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

    contract, events = headers
    contract = append_to_contract_header(contract, MAC)
    new_block = ACBlock(
        index=chain_with_blocks.get_last_bloc.index + 1,
        timestamp=datetime.datetime.now(),
        previous_hash=chain_with_blocks.get_last_bloc.compute_hash(),
        contract_header=contract,
    )
    chain_with_blocks.proof_of_work(new_block)
    assert chain_with_blocks.add_block(new_block=new_block)
    str_chain: list[dict] = [block.to_dict() for block in chain_with_blocks.chain]
    local_chain = ACBlockchain(difficulty=chain_with_blocks.difficulty)
    assert local_chain.create_blockchain_from_request(str_chain)
    assert len(local_chain.chain) == len(chain_with_blocks.chain)
    for local_block, original_block in zip(local_chain.chain, chain_with_blocks.chain):
        assert local_block == original_block
    # We check that the contract MAC is present and decodable
    assert local_chain.get_last_bloc.find_contract("MAC")
    # We add some transactions, and we check that the MAC can be executed during mining operations
    local_chain.add_new_transaction(random_resource_policies())
    assert local_chain.mine()
    df = local_chain.get_last_bloc.body.events
    assert not df.loc[df["transaction_type"] == "AUTHENTICATION"].empty
