// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "./interfaces/ERC4337Interfaces.sol";

contract HSMTokenPaymaster is Ownable {
    IEntryPoint public immutable entryPoint;
    IERC20 public immutable hsmToken;
    uint256 public tokenPerEth;

    event GasSpent(address indexed user, uint256 ethCost, uint256 tokenCost, bytes32 txHash);

    constructor(address _entryPoint, address _hsmToken, uint256 _tokenPerEth) {
        entryPoint = IEntryPoint(_entryPoint);
        hsmToken = IERC20(_hsmToken);
        tokenPerEth = _tokenPerEth;
    }

    function setConversionRate(uint256 _rate) external onlyOwner {
        tokenPerEth = _rate;
    }

    function validatePaymasterUserOp(
        UserOperation calldata userOp,
        bytes32 userOpHash,
        uint256 maxCost
    ) external view returns (bytes memory context) {
        require(msg.sender == address(entryPoint), "only EntryPoint");
        address sender = userOp.sender;
        uint256 requiredTokens = (maxCost * tokenPerEth) / 1 ether;
        require(hsmToken.balanceOf(sender) >= requiredTokens, "insufficient balance");
        return abi.encode(sender, requiredTokens, userOpHash);
    }

    function postOp(
        bytes calldata context,
        uint256 actualGasCost,
        uint256 /* actualGasUsedByPaymaster */
    ) external {
        require(msg.sender == address(entryPoint), "only EntryPoint");
        (address sender, uint256 requiredTokens, bytes32 userOpHash) =
            abi.decode(context, (address, uint256, bytes32));

        uint256 tokenCost = (actualGasCost * tokenPerEth) / 1 ether;
        if (tokenCost < requiredTokens) requiredTokens = tokenCost;

        // paymaster uplink covers gas now; tokens can be deducted off-chain
        emit GasSpent(sender, actualGasCost, requiredTokens, userOpHash);
    }

    receive() external payable {}
}

