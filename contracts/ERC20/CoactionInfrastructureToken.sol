// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/token/ERC20/extensions/ERC20Burnable.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/Pausable.sol";
import "@openzeppelin/contracts/token/ERC20/extensions/ERC20FlashMint.sol";

contract CoactionInfrastructureToken is
    ERC20,
    ERC20Burnable,
    Ownable(msg.sender),
    Pausable,
    ERC20FlashMint
{
    uint256 public lastMintedTimestamp;
    uint256 public initialMintAmount = 100000000 * 10 ** decimals(); // 100,000,000
    uint256 public decayRate = 2; // Changed to 2% of "total tokens left"
    uint256 public mintInterval = 30 days;
    uint256 public constant FULLY_DILUTED_SUPPLY = 1000000000 * 10 ** 18; // 1,000,000,000
    mapping(address => uint256) public stakedAmounts;
    address[] public stakers;
    uint256 public totalStaked;
    mapping(address => uint256) public claimableAmounts;

    constructor() ERC20("Coaction Infrastructure Token", "CIT") {
        _mint(msg.sender, 100000000 * 10 ** decimals());
        lastMintedTimestamp = block.timestamp;
    }

    function setClaimableAmount(
        address _user,
        uint256 _amount
    ) external onlyOwner {
        claimableAmounts[_user] = _amount;
    }

    // New function to claim tokens
    function claimTokens() external {
        uint256 amount = claimableAmounts[msg.sender];
        require(amount > 0, "Nothing to claim");
        claimableAmounts[msg.sender] = 0; // Reset claimable amount
        _mint(msg.sender, amount); // Mint the tokens
    }

    function stake(uint256 amount) public {
        require(amount > 0, "Cannot stake zero tokens");
        require(balanceOf(msg.sender) >= amount, "Insufficient balance");

        if (stakedAmounts[msg.sender] == 0) {
            stakers.push(msg.sender);
        }

        _transfer(msg.sender, address(this), amount);
        stakedAmounts[msg.sender] += amount;
        totalStaked += amount;
    }

    function getDecayedAmount() public view returns (uint256) {
        uint256 totalTokensLeft = FULLY_DILUTED_SUPPLY - totalSupply(); // Calculate "total tokens left"
        return (totalTokensLeft * decayRate) / 100;
    }

    function approveDistributor(
        address distributor,
        uint256 amount
    ) public onlyOwner {
        _approve(msg.sender, distributor, amount);
    }

    function unstake(uint256 amount) public {
        require(
            stakedAmounts[msg.sender] >= amount,
            "Insufficient staked balance"
        );

        _transfer(address(this), msg.sender, amount);
        stakedAmounts[msg.sender] -= amount;
        totalStaked -= amount;
    }

    function pause() public onlyOwner {
        _pause();
    }

    function unpause() public onlyOwner {
        _unpause();
    }

    function mint(address to, uint256 amount) public onlyOwner {
        require(
            totalSupply() + amount <= FULLY_DILUTED_SUPPLY,
            "Exceeds fully diluted supply"
        );
        _mint(to, amount);
    }

    function decayedMint(address to) public onlyOwner {
        //require(block.timestamp >= lastMintedTimestamp + mintInterval, "Not time to mint yet");

        uint256 totalTokensLeft = FULLY_DILUTED_SUPPLY - totalSupply(); // Calculate "total tokens left"
        uint256 decayedAmount = (totalTokensLeft * decayRate) / 100; // Calculate 2% of "total tokens left"

        require(
            totalSupply() + decayedAmount <= FULLY_DILUTED_SUPPLY,
            "Exceeds fully diluted supply"
        );

        uint256 stakingReward = (decayedAmount * 75) / 1000; // 7.5% of decayedAmount

        if (totalStaked > 0) {
            _mint(address(this), stakingReward);
            totalStaked += stakingReward; // Increase the total staked amount by the staking reward
        }

        _mint(to, decayedAmount - stakingReward); // Mint the remaining tokens to the specified address

        lastMintedTimestamp = block.timestamp; // Update the last minted timestamp
    }

    // This calculation will eventually be done off-chain
    function distributeStakingRewards() public onlyOwner {
        require(totalStaked > 0, "No tokens are staked");

        uint256 stakingReward = balanceOf(address(this));
        uint256 rewardPerToken = stakingReward / totalStaked;

        for (uint256 i = 0; i < stakers.length; i++) {
            address staker = stakers[i];
            uint256 reward = stakedAmounts[staker] * rewardPerToken;
            _transfer(address(this), staker, reward);
        }
    }
}
