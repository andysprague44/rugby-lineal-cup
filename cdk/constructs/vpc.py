from typing import Optional, List
from aws_cdk import Stack
from aws_cdk import Stack
from aws_cdk.aws_ec2 import (
    Vpc,
    IVpc,
    Subnet,
    SubnetSelection,
    SecurityGroup,
)
from ..config_base import ConfigBase


class MyVpc(Vpc):

    @staticmethod
    def resolve_vpc(stack: Stack, config: ConfigBase, vpc_id: str) -> Vpc | IVpc:
        """
        Locate the VPC that corresponds to the provided VPC id
        """
        id = f"{config.stack_name}-{vpc_id}-vpc"
        return Vpc.from_lookup(stack, id, vpc_id=vpc_id)

    @staticmethod
    def resolve_subnets(
        stack: Stack, config: ConfigBase, subnet_ids: List[str]
    ) -> Optional[SubnetSelection]:
        """
        TODO - do we want to allow for automatic subnet selection? lets not for now
        ...vpc.select_subnets(subnet_type=aws_ec2.SubnetType.PRIVATE_WITH_EGRESS)
        """
        prefix = f"{config.stack_name}-subnet"
        subnets = [
            Subnet.from_subnet_id(stack, f"{prefix}-{idx}", subnet_id)
            for idx, subnet_id in enumerate(subnet_ids)
        ]
        return SubnetSelection(subnets=subnets)


class MySecurityGroup(SecurityGroup):

    @staticmethod
    def resolve_security_group(
        stack: Stack,
        config: ConfigBase,
        vpc: Vpc,
        id: Optional[str],
        sg_id: Optional[str],
    ) -> SecurityGroup:
        if id is None:
            id = f"{config.stack_name}-sg"
        if sg_id is None:
            sg = SecurityGroup(
                stack,
                id,
                security_group_name=id,
                vpc=vpc,
                allow_all_outbound=False,
                disable_inline_rules=True,
            )
        else:
            sg = SecurityGroup.from_security_group_id(stack, id, sg_id)
        return sg

    @staticmethod
    def resolve_security_groups(
        stack: Stack, config: ConfigBase, vpc: Vpc, sg_ids: List[str]
    ) -> List[SecurityGroup]:
        sgs = []

        if sg_ids is None or len(sg_ids) == 0:
            return sgs
        for idx, sg_id in enumerate(sg_ids):
            id = f"{config.stack_name}-security-group-{idx}"
            sgs.append(
                MySecurityGroup.resolve_security_group(stack, config, vpc, id, sg_id)
            )

        return sgs
