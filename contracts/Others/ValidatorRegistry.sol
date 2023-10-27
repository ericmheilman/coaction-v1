// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";

contract ValidatorTreasury {
    struct ValidatorInfo {
        string sourceBlockchain;
        address operatorAddress;
        address rewardsAddress;
        uint256 rebatePercentage; // in basis points, i.e., 100 means 1%
        bool isSubscribed;
    }

    IERC20 public CIT;
    mapping(address => ValidatorInfo) public validators;
    mapping(address => uint256) public citBalances;
    ValidatorInfo[] public allValidators;

    event ValidatorRegistered(
        address indexed validator,
        string sourceBlockchain,
        uint256 rebatePercentage
    );
    event CommissionConverted(address indexed validator, uint256 amount);
    event Withdrawn(address indexed validator, uint256 amount);
    event Unsubscribed(address indexed validator);

    constructor(address _CITAddress) {
        CIT = IERC20(_CITAddress);
    }

    function registerValidator(
        string memory _sourceBlockchain, // LPT, GRT, etc.
        address _rewardsAddress,
        uint256 _rebatePercentage
    ) external {
        require(
            !validators[msg.sender].isSubscribed,
            "Validator already registered"
        );

        validators[msg.sender] = ValidatorInfo({
            sourceBlockchain: _sourceBlockchain,
            operatorAddress: msg.sender,
            rewardsAddress: _rewardsAddress,
            rebatePercentage: _rebatePercentage,
            isSubscribed: true
        });

        // Add the validator to the array
        allValidators.push(
            ValidatorInfo({
                sourceBlockchain: _sourceBlockchain,
                operatorAddress: msg.sender,
                rewardsAddress: _rewardsAddress,
                rebatePercentage: _rebatePercentage,
                isSubscribed: true
            })
        );

        emit ValidatorRegistered(
            msg.sender,
            _sourceBlockchain,
            _rebatePercentage
        );
    }

    function getValidators() external view returns (ValidatorInfo[] memory) {
        uint256 totalValidators = allValidators.length;
        ValidatorInfo[] memory result = new ValidatorInfo[](totalValidators);

        for (uint256 i = 0; i < totalValidators; i++) {
            address validatorAddress = allValidators[i].operatorAddress;
            result[i] = ValidatorInfo({
                sourceBlockchain: validators[validatorAddress].sourceBlockchain,
                operatorAddress: validators[validatorAddress].operatorAddress,
                rewardsAddress: validators[validatorAddress].rewardsAddress,
                rebatePercentage: validators[validatorAddress].rebatePercentage,
                isSubscribed: validators[validatorAddress].isSubscribed
            });
        }

        return result;
    }

    function convertCommissionToCIT(
        uint256 _commissionAmount
    ) external payable {
        require(
            validators[msg.sender].isSubscribed,
            "Validator not registered"
        );
        require(
            msg.value == _commissionAmount,
            "Sent ETH must match the commission amount"
        );

        uint256 citAmount = (_commissionAmount *
            validators[msg.sender].rebatePercentage) / 10000; // assuming rebatePercentage is in basis points

        // Assuming the contract has enough CIT to cover the conversion
        require(
            CIT.balanceOf(address(this)) >= citAmount,
            "Insufficient CIT in the contract"
        );

        // Update the CIT balance for the validator
        citBalances[msg.sender] += citAmount;

        emit CommissionConverted(msg.sender, citAmount);
    }

    function withdrawCIT(uint256 _amount) external {
        require(
            validators[msg.sender].isSubscribed,
            "Validator not registered"
        );
        require(citBalances[msg.sender] >= _amount, "Insufficient CIT balance");

        // Update the CIT balance for the validator
        citBalances[msg.sender] -= _amount;

        // Transfer CIT to the validator
        require(CIT.transfer(msg.sender, _amount), "CIT transfer failed");

        emit Withdrawn(msg.sender, _amount);
    }

    function unsubscribe() external {
        require(
            validators[msg.sender].isSubscribed,
            "Validator not registered"
        );

        // Mark the validator as unsubscribed
        validators[msg.sender].isSubscribed = false;

        emit Unsubscribed(msg.sender);
    }
}
