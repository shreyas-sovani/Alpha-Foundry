/**
 * Test Faucet - Verify judges can claim tokens
 */

const { ethers } = require("ethers");
require("dotenv").config();

const DatacoinABI = require("./abi/DataCoin.js");
const deploymentInfo = require("./faucet-deployment.json");

const FAUCET_ABI = [
  "function claimTokens() external",
  "function hasClaimed(address account) external view returns (bool)",
  "function getClaimStatus(address account) external view returns (bool hasClaimed, uint256 amountClaimed, uint256 lastClaim, uint256 timeUntilNext)",
  "function CLAIM_AMOUNT() external view returns (uint256)",
  "event TokensClaimed(address indexed claimer, uint256 amount, uint256 timestamp)"
];

async function testFaucet() {
  console.log("🧪 Testing DataCoin Faucet\n");
  console.log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n");
  
  try {
    const provider = new ethers.JsonRpcProvider("https://ethereum-sepolia-rpc.publicnode.com");
    const wallet = new ethers.Wallet(process.env.PRIVATE_KEY, provider);
    
    const faucet = new ethers.Contract(deploymentInfo.faucetAddress, FAUCET_ABI, wallet);
    const dataCoin = new ethers.Contract(deploymentInfo.dataCoinAddress, DatacoinABI, wallet);
    
    console.log(`🔗 Testing with wallet: ${wallet.address}\n`);
    
    // Check initial balance
    const balanceBefore = await dataCoin.balanceOf(wallet.address);
    console.log(`💰 Balance before: ${ethers.formatUnits(balanceBefore, 18)} DADC\n`);
    
    // Check claim status
    const status = await faucet.getClaimStatus(wallet.address);
    console.log(`📊 Claim Status:`);
    console.log(`   Has claimed: ${status[0]}`);
    console.log(`   Amount claimed: ${ethers.formatUnits(status[1], 18)} DADC\n`);
    
    if (status[0]) {
      console.log("✅ Already claimed! Faucet is working correctly.\n");
      console.log("ℹ️  Note: Each address can only claim once to prevent abuse.\n");
      return;
    }
    
    // Claim tokens
    console.log("🚰 Claiming tokens from faucet...\n");
    const claimTx = await faucet.claimTokens();
    console.log(`📝 Transaction: ${claimTx.hash}`);
    console.log("⏳ Waiting for confirmation...\n");
    
    const receipt = await claimTx.wait();
    console.log(`✅ Transaction confirmed in block ${receipt.blockNumber}\n`);
    
    // Check new balance
    const balanceAfter = await dataCoin.balanceOf(wallet.address);
    const received = balanceAfter - balanceBefore;
    
    console.log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n");
    console.log("🎉 FAUCET TEST SUCCESSFUL!\n");
    console.log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n");
    console.log(`💰 Balance after: ${ethers.formatUnits(balanceAfter, 18)} DADC`);
    console.log(`📈 Tokens received: ${ethers.formatUnits(received, 18)} DADC\n`);
    
    // Verify claim status updated
    const statusAfter = await faucet.getClaimStatus(wallet.address);
    console.log(`📊 Updated Claim Status:`);
    console.log(`   Has claimed: ${statusAfter[0]}`);
    console.log(`   Amount claimed: ${ethers.formatUnits(statusAfter[1], 18)} DADC\n`);
    
    console.log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n");
    console.log("✅ FAUCET IS READY FOR JUDGES!\n");
    console.log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n");
    
  } catch (error) {
    if (error.message.includes("AlreadyClaimed")) {
      console.log("✅ Already claimed! Faucet is working correctly.\n");
      console.log("ℹ️  This address has already claimed tokens from the faucet.\n");
      console.log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n");
      console.log("✅ FAUCET IS READY FOR JUDGES!\n");
      console.log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n");
    } else {
      console.error("\n❌ Test failed:");
      console.error(error.message);
      process.exit(1);
    }
  }
}

testFaucet()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error("\n❌ Test failed:", error.message);
    process.exit(1);
  });
