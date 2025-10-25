// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

/// @title HSMToken with PMZ-based adaptive minting
/// @notice Integrates the Principles of Metric Zonality (PMZ) gradient logic
contract HSMTokenPMZ is ERC20, Ownable {
    struct PMZVector {
        uint256 courage;
        uint256 dexterity;
        uint256 clauseMatter;
        uint256 audacity;
    }

    event PMZAdjusted(address indexed miner, uint256 newRewardRate, PMZVector metrics);

    mapping(address => PMZVector) public pmzVectors;
    mapping(address => uint256) public rewardRates;

    uint256 public baseRewardRate = 1e18; // 1 token base rate

    constructor(address initialOwner)
        ERC20("HSM Token (PMZ)", "HSMZ")
        Ownable(initialOwner)
    {}

    /// @notice Update PMZ vector for a miner (used by miner or paymaster)
    function updatePMZ(address miner, PMZVector memory vec) public onlyOwner {
        pmzVectors[miner] = vec;
        rewardRates[miner] = _calculatePMZReward(vec);
        emit PMZAdjusted(miner, rewardRates[miner], vec);
    }

    /// @dev Core PMZ algorithm — normalize to [0.5, 3.0] range
    function _calculatePMZReward(PMZVector memory vec)
        internal
        pure
        returns (uint256)
    {
        uint256 weighted =
            (vec.courage + vec.dexterity + vec.clauseMatter + vec.audacity) / 4;
        uint256 scaled = (weighted * 25) / 10; // scale factor
        return scaled * 1e16; // base multiplier
    }

    /// @notice Mint tokens based on latest PMZ metrics
    function mintWithPMZ(address to) external {
        PMZVector memory vec = pmzVectors[to];
        uint256 rate = rewardRates[to];
        if (rate == 0) rate = baseRewardRate;
        uint256 amount = (rate * 1 ether) / 1e18;
        _mint(to, amount);
    }

    /// @notice Utility: reset to base reward rate
    function resetPMZ(address miner) external onlyOwner {
        rewardRates[miner] = baseRewardRate;
    }
}

