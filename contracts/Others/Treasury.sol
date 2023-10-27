// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "./APIConsumer.sol";
import "@uniswap/v2-periphery/contracts/interfaces/IUniswapV2Router02.sol";
import "@chainlink/contracts/src/v0.8/ChainlinkClient.sol";
import "@chainlink/contracts/src/v0.8/ConfirmedOwner.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol"; // Import the IERC20 interface

contract CombinedConsumer is ChainlinkClient, ConfirmedOwner {
    using Chainlink for Chainlink.Request;

    // State variables for APIConsumer functionality
    uint256 public maxRebate;
    bytes32 private apiConsumerJobId;
    uint256 private apiConsumerFee;

    // State variables for MultiWordConsumer functionality
    uint256 public usdAgainstGRT;
    uint256 public usdAgainstLPT;
    APIConsumer public grtConsumer; // Create a public variable to store the APIConsumer instance
    APIConsumer public lptConsumer; // Create a public variable to store the APIConsumer instance

    mapping(address => mapping(string => uint256)) public maxRebates;
    mapping(address => uint256) public GRTDeposits;
    mapping(address => uint256) public LPTDeposits;

    // ERC20-compatible GRT and LPT token contracts
    IERC20 public grtToken;
    IERC20 public lptToken;
    IERC20 public citToken;
    IUniswapV2Router02 public uniswapRouter;
    address public stakingRewardsContract;

    // Struct to hold validator information
    struct ValidatorInfo {
        address validator;
        uint256 grtDeposit;
    }

    // Struct to hold depositor information
    struct DepositorInfo {
        address depositor;
        uint256 grtDeposit;
        uint256 lptDeposit;
    }

    // Events
    event RequestMaxRebate(bytes32 indexed requestId, uint256 maxRebate);
    event GRTDeposited(address indexed user, uint256 amount);
    event LPTDeposited(address indexed user, uint256 amount);
    event CITBurnedForGRT(
        address indexed user,
        uint256 CITAmount,
        uint256 GRTAmount
    );
    event CITBurnedForLPT(
        address indexed user,
        uint256 CITAmount,
        uint256 LPTAmount
    );

    constructor(
        address _grtToken,
        address _lptToken
    ) ConfirmedOwner(msg.sender) {
        setChainlinkToken(0x779877A7B0D9E8603169DdbD7836e478b4624789);
        setChainlinkOracle(0x6090149792dAAeE9D1D568c9f9a6F6B46AA29eFD);

        grtConsumer = new APIConsumer();
        lptConsumer = new APIConsumer();

        // Initialize job IDs and fees for both functionalities
        apiConsumerJobId = "ca98366cc7314957b8c012c72f05aeeb";
        apiConsumerFee = (1 * LINK_DIVISIBILITY) / 10;

        grtToken = IERC20(_grtToken);
        lptToken = IERC20(_lptToken);
    }

    function depositGRT(uint256 amount) external {
        require(
            grtToken.transferFrom(msg.sender, address(this), amount),
            "GRT transfer failed"
        );

        GRTDeposits[msg.sender] = GRTDeposits[msg.sender] += amount;
        emit GRTDeposited(msg.sender, amount);
    }

    function depositLPT(uint256 amount) external {
        require(
            lptToken.transferFrom(msg.sender, address(this), amount),
            "LPT transfer failed"
        );
        LPTDeposits[msg.sender] = LPTDeposits[msg.sender] += amount;
        emit LPTDeposited(msg.sender, amount);
    }

    function burnCITforGRT(uint256 CITAmount) external {
        require(
            maxRebates[msg.sender]["GRT"] != 0,
            "Call setMaxRebate for GRT first and wait for update"
        );
        require(
            citToken.transferFrom(msg.sender, address(this), CITAmount),
            "CIT transfer failed"
        );
        uint256 rate = getRate("GRT");
        uint256 GRTAmount = CITAmount * rate;

        require(
            grtToken.balanceOf(address(this)) >= GRTAmount,
            "Insufficient GRT in the contract"
        );
        require(
            grtToken.transfer(msg.sender, GRTAmount),
            "GRT transfer failed"
        );
        emit CITBurnedForGRT(msg.sender, CITAmount, GRTAmount);
    }

    // Function to get all LPT deposits along with validator addresses
    function getAllLPTDeposits(
        address[] memory validators
    ) external view returns (ValidatorInfo[] memory) {
        uint256 validatorCount = validators.length;
        ValidatorInfo[] memory validatorInfoList = new ValidatorInfo[](
            validatorCount
        );

        for (uint256 i = 0; i < validatorCount; i++) {
            address validator = validators[i];
            uint256 lptDeposit = LPTDeposits[validator];
            validatorInfoList[i] = ValidatorInfo(validator, lptDeposit);
        }

        return validatorInfoList;
    }

    // Function to get all deposits along with depositor addresses
    function getAllDeposits(
        address[] memory depositors
    ) external view returns (DepositorInfo[] memory) {
        uint256 depositorCount = depositors.length;
        DepositorInfo[] memory depositorInfoList = new DepositorInfo[](
            depositorCount
        );

        for (uint256 i = 0; i < depositorCount; i++) {
            address depositor = depositors[i];
            uint256 grtDeposit = GRTDeposits[depositor];
            uint256 lptDeposit = LPTDeposits[depositor];
            depositorInfoList[i] = DepositorInfo(
                depositor,
                grtDeposit,
                lptDeposit
            );
        }

        return depositorInfoList;
    }

    // Function to get all GRT deposits along with validator addresses
    function getAllGRTDeposits(
        address[] memory validators
    ) external view returns (ValidatorInfo[] memory) {
        uint256 validatorCount = validators.length;
        ValidatorInfo[] memory validatorInfoList = new ValidatorInfo[](
            validatorCount
        );

        for (uint256 i = 0; i < validatorCount; i++) {
            address validator = validators[i];
            uint256 grtDeposit = GRTDeposits[validator];
            validatorInfoList[i] = ValidatorInfo(validator, grtDeposit);
        }

        return validatorInfoList;
    }

    // Function to clear all GRT deposits
    function clearAllGRTDeposits(
        address[] memory validators
    ) external onlyOwner {
        uint256 validatorCount = validators.length;

        for (uint256 i = 0; i < validatorCount; i++) {
            address validator = validators[i];
            GRTDeposits[validator] = 0;
        }
    }

    // Function to clear all LPT deposits
    function clearAllLPTDeposits(
        address[] memory validators
    ) external onlyOwner {
        uint256 validatorCount = validators.length;

        for (uint256 i = 0; i < validatorCount; i++) {
            address validator = validators[i];
            LPTDeposits[validator] = 0;
        }
    }

    function getRate(string memory whichRate) public view returns (uint256) {
        if (keccak256(bytes(whichRate)) == keccak256(bytes("GRT"))) {
            return grtConsumer.grtPrice();
        } else if (keccak256(bytes(whichRate)) == keccak256(bytes("LPT"))) {
            return lptConsumer.lptPrice();
        } else {
            revert("Invalid rate specified");
        }
    }

    // Function to set the max rebate for a specific token
    function setMaxRebate(string memory token, uint256 amount) external {
        require(amount >= 0, "Max rebate must be non-negative");
        maxRebates[msg.sender][token] = amount;
    }

    // Function to check the max rebate for a specific token
    function getMaxRebate(string memory token) public view returns (uint256) {
        return maxRebates[msg.sender][token];
    }

    function burnCITforLPT(uint256 CITAmount) external {
        require(
            maxRebates[msg.sender]["LPT"] != 0,
            "Call setMaxRebate for LPT first and wait for update"
        );
        require(
            citToken.transferFrom(msg.sender, address(this), CITAmount),
            "CIT transfer failed"
        );
        uint256 rate = getRate("LPT");
        uint256 LPTAmount = CITAmount * rate;

        require(
            lptToken.balanceOf(address(this)) >= LPTAmount,
            "Insufficient LPT in the contract"
        );
        require(
            lptToken.transfer(msg.sender, LPTAmount),
            "LPT transfer failed"
        );
        emit CITBurnedForLPT(msg.sender, CITAmount, LPTAmount);
    }

    function convertTokensAndSendRewards() external {
        // Approve the Uniswap router to spend GRT and LPT
        //grtToken.approve(address(uniswapRouter), grtToken.balanceOf(address(this)));
        //lptToken.approve(address(uniswapRouter), lptToken.balanceOf(address(this)));

        // Convert GRT to CIT
        address[] memory pathGRT = new address[](2);
        pathGRT[0] = address(grtToken);
        pathGRT[1] = address(citToken);

        uniswapRouter.swapExactTokensForTokens(
            grtToken.balanceOf(address(this)),
            0,
            pathGRT,
            address(this),
            block.timestamp + 15
        );

        // Convert LPT to CIT
        address[] memory pathLPT = new address[](2);
        pathLPT[0] = address(lptToken);
        pathLPT[1] = address(citToken);
        uniswapRouter.swapExactTokensForTokens(
            lptToken.balanceOf(address(this)),
            0,
            pathLPT,
            address(this),
            block.timestamp + 15
        );

        // Send the CIT to the staking rewards contract
        uint256 CITBalance = citToken.balanceOf(address(this));
        require(
            citToken.transfer(stakingRewardsContract, CITBalance),
            "Transfer failed"
        );
    }

    function getGRTDepositsForValidator(
        address validator
    ) external view returns (uint256) {
        return GRTDeposits[validator];
    }

    function getLPTDepositsForValidator(
        address validator
    ) external view returns (uint256) {
        return LPTDeposits[validator];
    }

    // Transfer functions with maxRebate check
    function transferGRT(uint256 amount) public {
        require(amount <= maxRebate, "Amount exceeds max rebate");
        require(grtToken.transfer(msg.sender, amount), "Transfer failed");
    }

    function transferLPT(uint256 amount) public {
        require(amount <= maxRebate, "Amount exceeds max rebate");
        require(lptToken.transfer(msg.sender, amount), "Transfer failed");
    }

    // Common functionality
    function withdrawLink() public onlyOwner {
        LinkTokenInterface link = LinkTokenInterface(chainlinkTokenAddress());
        require(
            link.transfer(msg.sender, link.balanceOf(address(this))),
            "Unable to transfer"
        );
    }
}
