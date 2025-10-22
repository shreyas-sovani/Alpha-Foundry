// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

interface IDataCoin {
    function mint(address to, uint256 amount) external;
    function balanceOf(address account) external view returns (uint256);
}

/**
 * @title DataCoinFaucet
 * @notice Allows judges to self-claim DADC tokens for async hackathon evaluation
 * @dev This contract must have MINTER_ROLE on the DataCoin contract
 */
contract DataCoinFaucet {
    IDataCoin public immutable dataCoin;
    address public immutable owner;
    
    uint256 public constant CLAIM_AMOUNT = 100 * 10**18; // 100 DADC per claim
    uint256 public constant COOLDOWN_PERIOD = 1 hours; // Prevent spam
    
    mapping(address => uint256) public lastClaimTime;
    mapping(address => uint256) public totalClaimed;
    
    event TokensClaimed(address indexed claimer, uint256 amount, uint256 timestamp);
    event FaucetDrained(address indexed to, uint256 amount);
    
    error CooldownActive(uint256 timeRemaining);
    error AlreadyClaimed(uint256 amount);
    error Unauthorized();
    
    constructor(address _dataCoin) {
        dataCoin = IDataCoin(_dataCoin);
        owner = msg.sender;
    }
    
    /**
     * @notice Claim DADC tokens (judges call this directly)
     * @dev Mints 100 DADC to the caller if they haven't claimed before
     */
    function claimTokens() external {
        // Check if already claimed
        if (totalClaimed[msg.sender] > 0) {
            revert AlreadyClaimed(totalClaimed[msg.sender]);
        }
        
        // Check cooldown (if we allow multiple claims, uncomment)
        // uint256 timeSinceLastClaim = block.timestamp - lastClaimTime[msg.sender];
        // if (timeSinceLastClaim < COOLDOWN_PERIOD) {
        //     revert CooldownActive(COOLDOWN_PERIOD - timeSinceLastClaim);
        // }
        
        // Update state
        lastClaimTime[msg.sender] = block.timestamp;
        totalClaimed[msg.sender] += CLAIM_AMOUNT;
        
        // Mint tokens
        dataCoin.mint(msg.sender, CLAIM_AMOUNT);
        
        emit TokensClaimed(msg.sender, CLAIM_AMOUNT, block.timestamp);
    }
    
    /**
     * @notice Check if an address has already claimed
     */
    function hasClaimed(address account) external view returns (bool) {
        return totalClaimed[account] > 0;
    }
    
    /**
     * @notice Check time until next claim is available
     */
    function timeUntilNextClaim(address account) external view returns (uint256) {
        uint256 timeSinceLastClaim = block.timestamp - lastClaimTime[account];
        if (timeSinceLastClaim >= COOLDOWN_PERIOD) {
            return 0;
        }
        return COOLDOWN_PERIOD - timeSinceLastClaim;
    }
    
    /**
     * @notice Get claim status for an address
     */
    function getClaimStatus(address account) external view returns (
        bool hasClaimed,
        uint256 amountClaimed,
        uint256 lastClaim,
        uint256 timeUntilNext
    ) {
        hasClaimed = totalClaimed[account] > 0;
        amountClaimed = totalClaimed[account];
        lastClaim = lastClaimTime[account];
        
        uint256 timeSinceLastClaim = block.timestamp - lastClaimTime[account];
        timeUntilNext = timeSinceLastClaim >= COOLDOWN_PERIOD ? 0 : COOLDOWN_PERIOD - timeSinceLastClaim;
    }
    
    /**
     * @notice Emergency: Owner can recover any stuck tokens
     */
    function emergencyWithdraw() external {
        if (msg.sender != owner) revert Unauthorized();
        // This faucet doesn't hold tokens, it mints them
        // But we keep this for safety
    }
}
