/**
 * Mint DataCoins to Judge Addresses
 * 
 * After DataCoin creation with Strategy 1 (0% creator, 100% contributors),
 * use this script to mint tokens to judge addresses or a distribution contract.
 * 
 * As the creator, you automatically have MINTER_ROLE.
 */

const { ethers } = require("ethers");
require("dotenv").config();

const DatacoinABI = require("./abi/DataCoin.js");

// ============================================================================
// 🔧 CONFIGURATION
// ============================================================================

// DataCoin address from creation script output
const DATACOIN_ADDRESS = "0x8d302FfB73134235EBaD1B9Cd9C202d14f906FeC"; // DEXArb Data Coin

// Network configuration
const CHAIN_NAME = "sepolia";
const RPC_URL = process.env.SEPOLIA_RPC_URL || "https://ethereum-sepolia-rpc.publicnode.com";

// Minting configuration
// Option 1: Mint to multiple judge addresses
const MINT_TO_JUDGES = [
  { address: "0xJudge1Address", amount: "100" }, // 100 DADC
  { address: "0xJudge2Address", amount: "100" },
  { address: "0xJudge3Address", amount: "100" },
  // Add more judges as needed
];

// Option 2: Mint to a single distribution contract
const MINT_TO_DISTRIBUTION_CONTRACT = {
  enabled: false,
  address: "0xYourDistributionContractAddress",
  amount: "10000", // 10,000 DADC for distribution
};

// ============================================================================
// 🚀 MAIN EXECUTION
// ============================================================================

async function mintTokens() {
  try {
    console.log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
    console.log("🎯 DEXArb DataCoin Minting");
    console.log("   Minting tokens for async hackathon judges");
    console.log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n");

    // Validation
    if (DATACOIN_ADDRESS === "0xYourDataCoinAddressHere") {
      throw new Error("Please update DATACOIN_ADDRESS with your deployed DataCoin address");
    }

    // Setup connection
    console.log("🔗 Connecting to Sepolia...\n");
    const provider = new ethers.JsonRpcProvider(RPC_URL);
    const wallet = new ethers.Wallet(process.env.PRIVATE_KEY, provider);
    const datacoin = new ethers.Contract(DATACOIN_ADDRESS, DatacoinABI, wallet);

    console.log(`✅ Connected`);
    console.log(`   Wallet: ${wallet.address}`);
    console.log(`   DataCoin: ${DATACOIN_ADDRESS}\n`);

    // Check token info
    console.log("📊 DataCoin Information:\n");
    const name = await datacoin.name();
    const symbol = await datacoin.symbol();
    const creator = await datacoin.creator();
    const maxSupply = await datacoin.MAX_SUPPLY();
    const allocConfig = await datacoin.allocConfig();

    console.log(`   Name: ${name}`);
    console.log(`   Symbol: ${symbol}`);
    console.log(`   Creator: ${creator}`);
    console.log(`   Max Supply: ${ethers.formatUnits(maxSupply, 18)}`);
    console.log(`   Contributors Alloc: ${allocConfig[2] / 100}%\n`);

    // Verify you're the creator
    if (creator.toLowerCase() !== wallet.address.toLowerCase()) {
      throw new Error(`Only the creator can mint. Creator is ${creator}, you are ${wallet.address}`);
    }

    // Calculate total mint amount
    const contributorsAlloc = (maxSupply * BigInt(allocConfig[2])) / BigInt(10000);
    const contributorsAllocMinted = await datacoin.contributorsAllocMinted();
    const remaining = contributorsAlloc - contributorsAllocMinted;

    console.log("💰 Minting Capacity:\n");
    console.log(`   Total Contributors Allocation: ${ethers.formatUnits(contributorsAlloc, 18)} ${symbol}`);
    console.log(`   Already Minted: ${ethers.formatUnits(contributorsAllocMinted, 18)} ${symbol}`);
    console.log(`   Remaining: ${ethers.formatUnits(remaining, 18)} ${symbol}\n`);

    // Mint to distribution contract (Option 2)
    if (MINT_TO_DISTRIBUTION_CONTRACT.enabled) {
      console.log("🏭 Minting to distribution contract...\n");
      const amount = ethers.parseUnits(MINT_TO_DISTRIBUTION_CONTRACT.amount, 18);

      if (amount > remaining) {
        throw new Error("Requested amount exceeds remaining allocation");
      }

      console.log(`   Recipient: ${MINT_TO_DISTRIBUTION_CONTRACT.address}`);
      console.log(`   Amount: ${MINT_TO_DISTRIBUTION_CONTRACT.amount} ${symbol}`);

      const tx = await datacoin.mint(MINT_TO_DISTRIBUTION_CONTRACT.address, amount);
      console.log(`   Transaction: ${tx.hash}`);
      await tx.wait();
      console.log(`   ✅ Minted successfully!\n`);
    }

    // Mint to individual judges (Option 1)
    if (!MINT_TO_DISTRIBUTION_CONTRACT.enabled) {
      console.log("👥 Minting to judge addresses...\n");

      let totalMinted = BigInt(0);
      const results = [];

      for (const judge of MINT_TO_JUDGES) {
        if (judge.address.includes("Judge") || judge.address.includes("0xJudge")) {
          console.log(`   ⚠️  Skipping placeholder address: ${judge.address}`);
          continue;
        }

        const amount = ethers.parseUnits(judge.amount, 18);

        if (totalMinted + amount > remaining) {
          console.log(`   ⚠️  Skipping ${judge.address} (would exceed allocation)`);
          continue;
        }

        console.log(`   Minting to ${judge.address}...`);
        const tx = await datacoin.mint(judge.address, amount);
        console.log(`      Transaction: ${tx.hash}`);
        await tx.wait();
        console.log(`      ✅ Minted ${judge.amount} ${symbol}`);

        totalMinted += amount;
        results.push({
          address: judge.address,
          amount: judge.amount,
          tx: tx.hash,
        });
      }

      console.log("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
      console.log("📊 MINTING SUMMARY");
      console.log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n");

      console.log(`   Total Recipients: ${results.length}`);
      console.log(`   Total Minted: ${ethers.formatUnits(totalMinted, 18)} ${symbol}\n`);

      console.log("Recipients:");
      results.forEach((r, i) => {
        console.log(`   ${i + 1}. ${r.address}: ${r.amount} ${symbol}`);
      });
      console.log("\n");
    }

    // Check balances
    console.log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
    console.log("✅ MINTING COMPLETED!");
    console.log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n");

    // Final statistics
    const newContributorsAllocMinted = await datacoin.contributorsAllocMinted();
    const newRemaining = contributorsAlloc - newContributorsAllocMinted;

    console.log("📈 Final Statistics:\n");
    console.log(`   Total Minted: ${ethers.formatUnits(newContributorsAllocMinted, 18)} ${symbol}`);
    console.log(`   Remaining: ${ethers.formatUnits(newRemaining, 18)} ${symbol}`);
    console.log(`   Utilization: ${(Number(newContributorsAllocMinted) / Number(contributorsAlloc) * 100).toFixed(2)}%\n`);

  } catch (error) {
    console.error("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
    console.error("❌ ERROR OCCURRED");
    console.error("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n");
    console.error(error.message);

    if (error.code) {
      console.error(`   Error code: ${error.code}\n`);
    }

    process.exit(1);
  }
}

// ============================================================================
// 🎬 SCRIPT EXECUTION
// ============================================================================

console.log("\n🚀 DEXArb DataCoin Minting Script\n");

mintTokens()
  .then(() => {
    console.log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
    console.log("✅ SCRIPT COMPLETED SUCCESSFULLY!");
    console.log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n");
    process.exit(0);
  })
  .catch((error) => {
    console.error("\n💥 Script failed:", error.message);
    process.exit(1);
  });
