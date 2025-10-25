// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import {UserOperation, IEntryPoint} from "./interfaces/ERC4337Interfaces.sol";

contract HSMTokenPaymaster is Ownable {
    IEntryPoint public immutable entryPoint;
    IERC20 public immutable hsmToken;
    uint256 public tokenPerEth;     // conversion rate: how many HSM tokens equal 1 ETH gas
    mapping(address => bool) public approvedWallet;

    constructor(address _entryPoint, address _hsmToken, uint256 _tokenPerEth) {
        entryPoint = IEntryPoint(_entryPoint);
        hsmToken = IERC20(_hsmToken);
        tokenPerEth = _tokenPerEth;
    }

    function setConversionRate(uint256 _rate) external onlyOwner {
        tokenPerEth = _rate;
    }

    function approveWallet(address wallet, bool ok) external onlyOwner {
        approvedWallet[wallet] = ok;
    }

    /// Called by EntryPoint: validate if this paymaster will cover the gas.
    function validatePaymasterUserOp(
        UserOperation calldata userOp,
        bytes32 /*userOpHash*/,
        uint256 maxCost
    ) external returns (bytes memory context) {
        require(msg.sender == address(entryPoint), "only EntryPoint");
        address sender = userOp.sender;
        require(approvedWallet[sender], "wallet not approved");
        // compute required token amount
        uint256 requiredTokens = (maxCost * tokenPerEth) / 1 ether;
        require(hsmToken.balanceOf(sender) >= requiredTokens, "not enough HSM tokens");
        // we don't take tokens yet-will do postOp
        return abi.encode(sender, requiredTokens);
    }

    /// Called after execution: collect those tokens.
    function postOp(
        bytes calldata context,
        uint256 actualGasCost,
        uint256 /*actualGasUsedByPaymaster*/
    ) external {
        require(msg.sender == address(entryPoint), "only EntryPoint");
        (address sender, uint256 requiredTokens) = abi.decode(context, (address, uint256));
        // compute actual token cost
        uint256 tokenCost = (actualGasCost * tokenPerEth) / 1 ether;
        if (tokenCost < requiredTokens) {
            // refund difference or just collect tokenCost
            requiredTokens = tokenCost;
        }
        require(hsmToken.transferFrom(sender, address(this), requiredTokens), "token transfer failed");
    }

    /// Owner can withdraw tokens
    function withdrawTokens(address to, uint256 amount) external onlyOwner {
        hsmToken.transfer(to, amount);
    }

    /// Owner can fund contract with ETH so EntryPoint can pay gas
    receive() external payable {}
}

