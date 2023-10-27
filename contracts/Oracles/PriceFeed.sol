// SPDX-License-Identifier: MIT
pragma solidity ^0.8.7;

import "@chainlink/contracts/src/v0.8/ChainlinkClient.sol";
import "@chainlink/contracts/src/v0.8/ConfirmedOwner.sol";

contract APIConsumer is ChainlinkClient, ConfirmedOwner {
    using Chainlink for Chainlink.Request;

    uint256 public grtPrice;
    uint256 public lptPrice;
    bytes32 private grtJobId;
    bytes32 private lptJobId;
    uint256 private fee;

    event RequestGRTPrice(bytes32 indexed requestId, uint256 price);
    event RequestLPTPrice(bytes32 indexed requestId, uint256 price);

    constructor() ConfirmedOwner(msg.sender) {
        setChainlinkToken(0x779877A7B0D9E8603169DdbD7836e478b4624789);
        setChainlinkOracle(0x6090149792dAAeE9D1D568c9f9a6F6B46AA29eFD);

        // Set the job IDs and fee (you might need to obtain the actual job IDs)
        grtJobId = "ca98366cc7314957b8c012c72f05aeeb";
        lptJobId = "ca98366cc7314957b8c012c72f05aeeb";
        fee = (1 * LINK_DIVISIBILITY) / 10; // 0.1 LINK (Varies by network and job)
    }

    // Request GRT price data from the API
    function requestGRTPriceData() public returns (bytes32 requestId) {
        Chainlink.Request memory req = buildChainlinkRequest(
            grtJobId,
            address(this),
            this.fulfillGRT.selector
        );

        // Set the URL to perform the GET request on
        req.add(
            "get",
            "https://min-api.cryptocompare.com/data/pricemultifull?fsyms=GRT&tsyms=USD"
        );

        // Set the path to find the desired data in the API response
        req.add("path", "RAW,GRT,USD,PRICE");

        // Multiply the result by 10^18 to remove decimals
        req.addInt("times", 10 ** 18);

        // Sends the request
        return sendChainlinkRequest(req, fee);
    }

    // Request LPT price data from the API
    function requestLPTPriceData() public returns (bytes32 requestId) {
        Chainlink.Request memory req = buildChainlinkRequest(
            lptJobId,
            address(this),
            this.fulfillLPT.selector
        );

        // Set the URL to perform the GET request on
        req.add(
            "get",
            "https://min-api.cryptocompare.com/data/pricemultifull?fsyms=LPT&tsyms=USD"
        );

        // Set the path to find the desired data in the API response
        req.add("path", "RAW,LPT,USD,PRICE");

        // Multiply the result by 10^18 to remove decimals
        req.addInt("times", 10 ** 18);

        // Sends the request
        return sendChainlinkRequest(req, fee);
    }

    // Receive the response for GRT price
    function fulfillGRT(
        bytes32 _requestId,
        uint256 _price
    ) public recordChainlinkFulfillment(_requestId) {
        emit RequestGRTPrice(_requestId, _price);
        grtPrice = _price;
    }

    // Receive the response for LPT price
    function fulfillLPT(
        bytes32 _requestId,
        uint256 _price
    ) public recordChainlinkFulfillment(_requestId) {
        emit RequestLPTPrice(_requestId, _price);
        lptPrice = _price;
    }

    // Allow withdraw of Link tokens from the contract
    function withdrawLink() public onlyOwner {
        LinkTokenInterface link = LinkTokenInterface(chainlinkTokenAddress());
        require(
            link.transfer(msg.sender, link.balanceOf(address(this))),
            "Unable to transfer"
        );
    }
}
