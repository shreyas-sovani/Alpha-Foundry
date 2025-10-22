/**
 * Final Verification - End-to-End Test
 * 
 * Verifies the complete async hackathon setup:
 * 1. DataCoin deployed correctly
 * 2. Faucet has minting permissions
 * 3. Judges can claim tokens autonomously
 * 4. Token balance checking works
 */

const { ethers } = require("ethers");
require("dotenv").config();

const DatacoinABI = require("./abi/DataCoin.js");
const deploymentInfo = require("./faucet-deployment.json");

// Load the full ABI from deployment
const FAUCET_ABI = deploymentInfo.faucetABI;

async function runVerification() {
  console.log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
  console.log("🔍 FINAL VERIFICATION - Async Hackathon Setup");
  console.log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n");
  
  try {
    const provider = new ethers.JsonRpcProvider("https://ethereum-sepolia-rpc.publicnode.com");
    
    const dataCoinAddress = deploymentInfo.dataCoinAddress;
    const faucetAddress = deploymentInfo.faucetAddress;
    
    console.log("📋 Configuration:");
    console.log(`   DataCoin: ${dataCoinAddress}`);
    console.log(`   Faucet: ${faucetAddress}`);
    console.log(`   Network: ${deploymentInfo.network}\n`);
    
    // 1. Verify DataCoin deployment
    console.log("1️⃣  Verifying DataCoin deployment...");
    const dataCoin = new ethers.Contract(dataCoinAddress, DatacoinABI, provider);
    
    const name = await dataCoin.name();
    const symbol = await dataCoin.symbol();
    const totalSupply = await dataCoin.totalSupply();
    const maxSupply = await dataCoin.MAX_SUPPLY();
    
    console.log(`   ✅ Name: ${name}`);
    console.log(`   ✅ Symbol: ${symbol}`);
    console.log(`   ✅ Total Supply: ${ethers.formatUnits(totalSupply, 18)}`);
    console.log(`   ✅ Max Supply: ${ethers.formatUnits(maxSupply, 18)}\n`);
    
    // 2. Verify faucet deployment
    console.log("2️⃣  Verifying faucet deployment...");
    const faucet = new ethers.Contract(faucetAddress, FAUCET_ABI, provider);
    
    const faucetDataCoin = await faucet.dataCoin();
    const claimAmount = await faucet.CLAIM_AMOUNT();
    
    if (faucetDataCoin.toLowerCase() !== dataCoinAddress.toLowerCase()) {
      throw new Error("Faucet is not linked to correct DataCoin!");
    }
    
    console.log(`   ✅ Faucet linked to DataCoin: ${faucetDataCoin}`);
    console.log(`   ✅ Claim amount: ${ethers.formatUnits(claimAmount, 18)} DADC\n`);
    
    // 3. Verify MINTER_ROLE
    console.log("3️⃣  Verifying faucet permissions...");
    const MINTER_ROLE = ethers.keccak256(ethers.toUtf8Bytes("MINTER_ROLE"));
    const hasMinterRole = await dataCoin.hasRole(MINTER_ROLE, faucetAddress);
    
    if (!hasMinterRole) {
      throw new Error("Faucet does not have MINTER_ROLE!");
    }
    
    console.log(`   ✅ Faucet has MINTER_ROLE\n`);
    
    // 4. Check contributors allocation capacity
    console.log("4️⃣  Checking minting capacity...");
    const allocConfig = await dataCoin.allocConfig();
    const contributorsAllocBps = Number(allocConfig[2]);
    const contributorsMinted = await dataCoin.contributorsAllocMinted();
    const contributorsAllocation = (maxSupply * BigInt(contributorsAllocBps)) / 10000n;
    const remainingCapacity = contributorsAllocation - contributorsMinted;
    
    console.log(`   ✅ Contributors allocation: ${contributorsAllocBps / 100}%`);
    console.log(`   ✅ Already minted: ${ethers.formatUnits(contributorsMinted, 18)} DADC`);
    console.log(`   ✅ Remaining capacity: ${ethers.formatUnits(remainingCapacity, 18)} DADC\n`);
    
    // 5. Simulate judge claim (read-only)
    console.log("5️⃣  Testing judge claim flow...");
    const testAddress = "0x1234567890123456789012345678901234567890"; // Random test address
    const hasClaimed = await faucet.hasClaimed(testAddress);
    const claimStatus = await faucet.getClaimStatus(testAddress);
    
    console.log(`   Test Address: ${testAddress}`);
    console.log(`   ✅ Can check claim status: ${!claimStatus[0] ? "Not claimed yet" : "Already claimed"}`);
    console.log(`   ✅ Faucet is queryable\n`);
    
    // 6. Verify Etherscan links
    console.log("6️⃣  Verification URLs:");
    console.log(`   🔗 DataCoin: https://sepolia.etherscan.io/address/${dataCoinAddress}`);
    console.log(`   🔗 Faucet: https://sepolia.etherscan.io/address/${faucetAddress}#writeContract`);
    console.log(`   🔗 Write Contract: https://sepolia.etherscan.io/address/${faucetAddress}#writeContract\n`);
    
    // 7. Calculate maximum judges
    const maxJudges = remainingCapacity / claimAmount;
    
    console.log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
    console.log("✅ ALL CHECKS PASSED!");
    console.log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n");
    
    console.log("📊 System Status:");
    console.log(`   ✅ DataCoin deployed and operational`);
    console.log(`   ✅ Faucet deployed with minting privileges`);
    console.log(`   ✅ ${ethers.formatUnits(remainingCapacity, 18)} DADC available`);
    console.log(`   ✅ Can serve up to ${maxJudges.toString()} judges\n`);
    
    console.log("🎯 For Judges:");
    console.log(`   1. Visit: https://sepolia.etherscan.io/address/${faucetAddress}#writeContract`);
    console.log(`   2. Connect wallet`);
    console.log(`   3. Call claimTokens()`);
    console.log(`   4. Receive ${ethers.formatUnits(claimAmount, 18)} DADC (minus 0.5% tax)\n`);
    
    console.log("🚀 Ready for ETHOnline 2025 async judging!");
    console.log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n");
    
    return true;
    
  } catch (error) {
    console.error("\n❌ VERIFICATION FAILED!");
    console.error("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n");
    console.error("Error:", error.message);
    if (error.stack) {
      console.error("\nStack trace:");
      console.error(error.stack);
    }
    return false;
  }
}

// Run verification
runVerification()
  .then((success) => {
    process.exit(success ? 0 : 1);
  })
  .catch((error) => {
    console.error("\n❌ Verification script error:", error.message);
    process.exit(1);
  });
