/**
 * DEXArb DataCoin Creation Script
 * 
 * Creates a DataCoin for DEXArb platform using Strategy 1:
 * - 0% creator allocation (no vesting)
 * - 100% contributors allocation (immediate access)
 * - 0% liquidity allocation (no Uniswap pool)
 * 
 * This allows immediate minting after creation for async hackathon judging.
 */

const { ethers } = require("ethers");
const bcrypt = require("bcrypt");
require("dotenv").config();

// Import ABIs from data-dao-deployment repo
const DatacoinFactoryABI = require("./abi/DataCoinFactory.js");
const DatacoinABI = require("./abi/DataCoin.js");
const ERC20ABI = require("./abi/ERC20.js");

// ============================================================================
// 🔧 CONFIGURATION - EDIT THESE VALUES
// ============================================================================

// 🌐 BLOCKCHAIN CONFIGURATION
const chainName = "sepolia"; // Sepolia testnet for ETHOnline 2025

// 💰 DATACOIN BASIC INFORMATION
const name = "DEXArb Data Coin";
const symbol = "DADC";
const description = "DataCoin for DEXArb platform - ETHOnline 2025 Lighthouse Prize";
const image = "ipfs://bafybeih5j5recyxiwscbtjl7o5rmv22rijmeq552iovrguas45s4766yw4";
const email = "shreyas2006.spam@gmail.com";
const telegram = "shreyas_dexarb";

// IPFS Metadata URI (uploaded to Lighthouse Storage)
// Format: ipfs://QmXXX...
const tokenURI = "ipfs://bafkreie73wguaf7yucgzcudbkivtgtxzvyv2efjg24s76j67lu7cbt7vcy";

// 👤 CREATOR CONFIGURATION
const creatorAddress = "0xD2aA21AF4faa840Dea890DB2C6649AACF2C80Ff3"; // Your wallet address

// 📊 ALLOCATION CONFIGURATION - STRATEGY 1 (Modified for factory fees)
// This configuration avoids vesting by setting creator allocation to 0%
// Small liquidity allocation is required for factory creation fees
const creatorAllocationBps = 0;      // 0% - No creator allocation = no vesting
const contributorsAllocationBps = 9900; // 99% - Maximum tokens for minting
const liquidityAllocationBps = 100;  // 1% - Minimal liquidity for factory fees
const creatorVesting = 1;            // Minimum 1 second (not used when creator allocation is 0)

// 🔒 LOCK ASSET CONFIGURATION
// LSDC on Sepolia requires 10,000 tokens minimum lock
const lockAsset = "LSDC";
const lockAmount = 10000; // Must be >= 10,000 LSDC

// ============================================================================
// 📦 CONSTANTS & CONFIGURATION
// ============================================================================

const basisPoints = 10000; // 100%

// Network configurations
const RPC_URLs = {
  sepolia: process.env.SEPOLIA_RPC_URL || "https://ethereum-sepolia-rpc.publicnode.com",
};

const FactoryAddresses = {
  sepolia: "0xC7Bc3432B0CcfeFb4237172340Cd8935f95f2990",
};

const approvedLockAssets = {
  sepolia: {
    USDC: {
      address: "0x1c7D4B196Cb0C7B01d743Fbc6116a902379C7238",
      decimal: 6,
      minLockAmount: 500000, // 0.5 USDC
    },
    WETH: {
      address: "0x7b79995e5f793A07Bc00c21412e50Ecae098E7f9",
      decimal: 18,
      minLockAmount: 100000000000000, // 0.0001 WETH
    },
    LSDC: {
      address: "0x2EA104BCdF3A448409F2dc626e606FdCf969a5aE",
      decimal: 18,
      minLockAmount: 10000000000000000000000, // 10,000 LSDC
    },
  },
};

// ============================================================================
// 🔍 VALIDATION FUNCTIONS
// ============================================================================

function validateInputs() {
  console.log("🔍 Validating configuration...\n");

  const errors = [];

  // Basic field validation
  if (!name.trim()) errors.push("❌ Name is required");
  if (!symbol.trim()) errors.push("❌ Symbol is required");
  if (!description.trim()) errors.push("❌ Description is required");
  if (!image.trim() || image.includes("your-image-url")) {
    errors.push("❌ Image URL is required (upload logo to Lighthouse first)");
  }
  if (!email.trim() || email.includes("your-email")) {
    errors.push("❌ Email is required");
  }
  if (!telegram.trim() || telegram.includes("your_telegram")) {
    errors.push("❌ Telegram handle is required");
  }
  if (!tokenURI.trim() || tokenURI.includes("Example")) {
    errors.push("❌ TokenURI is required (upload metadata to IPFS first)");
  }

  // Allocation validation
  const totalAllocation =
    creatorAllocationBps + contributorsAllocationBps + liquidityAllocationBps;
  if (totalAllocation !== basisPoints) {
    errors.push(
      `❌ Total allocation must equal 100% (10000 basis points). Current: ${totalAllocation}`
    );
  }

  // Verify Strategy 1 configuration (modified for factory fees)
  // Creator must be 0% to avoid vesting, small liquidity required for factory fees
  if (creatorAllocationBps !== 0) {
    errors.push("❌ Strategy 1 requires creator allocation = 0% (no vesting)");
  }
  if (contributorsAllocationBps < 9900) {
    errors.push("❌ Contributors allocation must be >= 99% for Strategy 1");
  }

  // Private key check
  if (!process.env.PRIVATE_KEY) {
    errors.push("❌ PRIVATE_KEY not found in .env file");
  }

  if (errors.length > 0) {
    console.error("🚨 Validation Errors:\n");
    errors.forEach((error) => console.error(error));
    throw new Error("Configuration validation failed");
  }

  console.log("✅ Configuration validated successfully");
  console.log("\n📋 Configuration Summary:");
  console.log(`   Name: ${name}`);
  console.log(`   Symbol: ${symbol}`);
  console.log(`   Creator: ${creatorAddress}`);
  console.log(`   Strategy: 1 (0% creator, 100% contributors)`);
  console.log(`   Lock Asset: ${lockAmount} ${lockAsset}`);
  console.log(`   Network: ${chainName}\n`);
}

function validateLockAsset() {
  console.log("🔒 Validating lock asset configuration...\n");

  const lockAssetConfig = approvedLockAssets[chainName][lockAsset];
  if (!lockAssetConfig) {
    throw new Error(`Lock asset ${lockAsset} not available on ${chainName}`);
  }

  const lockAmountInWei = lockAmount * Math.pow(10, lockAssetConfig.decimal);
  if (lockAmountInWei < lockAssetConfig.minLockAmount) {
    const minRequired =
      lockAssetConfig.minLockAmount / Math.pow(10, lockAssetConfig.decimal);
    throw new Error(
      `Lock amount (${lockAmount}) is below minimum required (${minRequired} ${lockAsset})`
    );
  }

  console.log(`✅ Lock asset validated`);
  console.log(`   Asset: ${lockAsset}`);
  console.log(`   Address: ${lockAssetConfig.address}`);
  console.log(`   Amount: ${lockAmount} ${lockAsset}`);
  console.log(`   Decimals: ${lockAssetConfig.decimal}\n`);

  return lockAssetConfig;
}

// ============================================================================
// 🚀 MAIN EXECUTION FUNCTION
// ============================================================================

async function createDataCoin() {
  try {
    console.log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
    console.log("🎯 DEXArb DataCoin Creation");
    console.log("   ETHOnline 2025 - Lighthouse Prize Track");
    console.log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n");

    // Step 1: Validate inputs
    validateInputs();

    // Step 2: Validate lock asset
    const lockAssetConfig = validateLockAsset();

    // Step 3: Setup blockchain connection
    console.log("🔗 Connecting to Sepolia network...\n");
    const rpc = RPC_URLs[chainName];
    const factoryAddress = FactoryAddresses[chainName];
    const provider = new ethers.JsonRpcProvider(rpc);
    const wallet = new ethers.Wallet(process.env.PRIVATE_KEY, provider);

    console.log(`✅ Connected to ${chainName}`);
    console.log(`   Wallet: ${wallet.address}`);
    console.log(`   Factory: ${factoryAddress}\n`);

    // Step 4: Setup contracts
    const factoryContract = new ethers.Contract(
      factoryAddress,
      DatacoinFactoryABI,
      wallet
    );

    const lockTokenContract = new ethers.Contract(
      lockAssetConfig.address,
      ERC20ABI,
      wallet
    );

    // Step 5: Check LSDC balance
    console.log("💰 Checking LSDC balance...\n");
    const balance = await lockTokenContract.balanceOf(wallet.address);
    const requiredAmount = ethers.parseUnits(
      lockAmount.toString(),
      lockAssetConfig.decimal
    );

    console.log(`   Your balance: ${ethers.formatUnits(balance, lockAssetConfig.decimal)} ${lockAsset}`);
    console.log(`   Required: ${lockAmount} ${lockAsset}`);

    if (balance < requiredAmount) {
      throw new Error(
        `Insufficient ${lockAsset} balance. Need ${lockAmount} ${lockAsset}, have ${ethers.formatUnits(balance, lockAssetConfig.decimal)}`
      );
    }
    console.log(`   ✅ Sufficient balance\n`);

    // Step 6: Approve token spending
    console.log("🔓 Approving LSDC spending...\n");
    const approveTx = await lockTokenContract.approve(
      factoryAddress,
      requiredAmount
    );
    console.log(`   Transaction: ${approveTx.hash}`);
    await approveTx.wait();
    console.log(`   ✅ Approval confirmed\n`);

    // Step 7: Generate salt for unique deployment
    console.log("🧂 Generating deployment salt...\n");
    const salt = await bcrypt.genSalt(10);
    const saltHash = ethers.keccak256(ethers.toUtf8Bytes(salt));
    console.log(`   ✅ Salt generated\n`);

    // Step 8: Create DataCoin
    console.log("🏗️  Creating DEXArb DataCoin...\n");
    console.log("   ⚙️  Configuration:");
    console.log("      • Creator Allocation: 0% (no vesting)");
    console.log("      • Contributors Allocation: 100% (immediate minting)");
    console.log("      • Liquidity Allocation: 0% (no Uniswap pool)");
    console.log("      • Strategy: Optimized for async hackathon\n");

    const createTx = await factoryContract.createDataCoin(
      name,
      symbol,
      tokenURI,
      creatorAddress,
      creatorAllocationBps,
      creatorVesting,
      contributorsAllocationBps,
      liquidityAllocationBps,
      lockAssetConfig.address,
      requiredAmount,
      saltHash
    );

    console.log(`   📝 Transaction: ${createTx.hash}`);
    console.log("   ⏳ Waiting for confirmation...\n");

    const receipt = await createTx.wait();

    // Step 9: Extract creation results
    console.log("✅ Transaction confirmed!\n");
    console.log("🔍 Extracting deployment details...\n");

    // Find DataCoinCreated event
    const dataCoinCreatedEvent = receipt.logs.find(
      (log) =>
        log.topics[0] ===
        ethers.id(
          "DataCoinCreated(address,address,address,string,string,string,address,uint256)"
        )
    );

    if (dataCoinCreatedEvent) {
      const decodedEvent = factoryContract.interface.decodeEventLog(
        "DataCoinCreated",
        dataCoinCreatedEvent.data,
        dataCoinCreatedEvent.topics
      );

      console.log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
      console.log("🎉 DATACOIN SUCCESSFULLY CREATED!");
      console.log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n");

      console.log("📋 Deployment Details:\n");
      console.log(`   🪙  DataCoin Address: ${decodedEvent.coinAddress}`);
      console.log(`   💧  Pool Address: ${decodedEvent.poolAddress}`);
      console.log(`   👤  Creator: ${decodedEvent.creator}`);
      console.log(`   🔒  Lock Token: ${decodedEvent.lockToken}`);
      console.log(`   📝  Name: ${decodedEvent.name}`);
      console.log(`   🏷️  Symbol: ${decodedEvent.symbol}`);
      console.log(`   🔗  TokenURI: ${decodedEvent.tokenURI}`);
      console.log(`   📦  Transaction: ${receipt.hash}`);
      console.log(`   🌐  Network: ${chainName}`);
      console.log(`   ⛽  Gas Used: ${receipt.gasUsed.toString()}`);
      console.log(`   🧱  Block: ${receipt.blockNumber}\n`);

      // Save deployment info
      const deploymentInfo = {
        network: chainName,
        timestamp: new Date().toISOString(),
        dataCoinAddress: decodedEvent.coinAddress,
        poolAddress: decodedEvent.poolAddress,
        creator: decodedEvent.creator,
        lockAsset: lockAsset,
        lockAmount: lockAmount,
        transactionHash: receipt.hash,
        blockNumber: receipt.blockNumber,
        allocation: {
          creator: "0%",
          contributors: "100%",
          liquidity: "0%",
        },
        vesting: "None (Strategy 1: 0% creator allocation)",
      };

      console.log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
      console.log("📝 NEXT STEPS FOR ASYNC HACKATHON");
      console.log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n");

      console.log("1️⃣  MINT TOKENS FOR JUDGES:");
      console.log(`    Run: node scripts/mintTokens.js`);
      console.log(`    This will mint tokens to designated addresses\n`);

      console.log("2️⃣  UPDATE FRONTEND:");
      console.log(`    Add DataCoin address to your unlock.html:`);
      console.log(`    const DATACOIN_ADDRESS = "${decodedEvent.coinAddress}";\n`);

      console.log("3️⃣  VERIFY ON ETHERSCAN:");
      console.log(`    https://sepolia.etherscan.io/address/${decodedEvent.coinAddress}\n`);

      console.log("4️⃣  FOR SUBMISSION:");
      console.log(`    • DataCoin Address: ${decodedEvent.coinAddress}`);
      console.log(`    • Created via 1MB.io platform (official factory)`);
      console.log(`    • 10,000 LSDC locked`);
      console.log(`    • Judges can receive tokens via minting\n`);

      console.log("💾 Deployment Info (save this):\n");
      console.log(JSON.stringify(deploymentInfo, null, 2));
      console.log("\n");

    } else {
      console.error("⚠️  Could not parse event data");
      console.log(`   Check transaction: https://sepolia.etherscan.io/tx/${receipt.hash}\n`);
    }

  } catch (error) {
    console.error("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
    console.error("❌ ERROR OCCURRED");
    console.error("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n");
    console.error(error.message);

    if (error.message.includes("InvalidVestingDuration")) {
      console.error("\n💡 WORKAROUND:");
      console.error("   The contract might enforce minimum vesting.");
      console.error("   Try editing the script to use:");
      console.error("   • creatorAllocationBps = 1000 (10%)");
      console.error("   • contributorsAllocationBps = 9000 (90%)");
      console.error("   • creatorVesting = 1 (1 second)");
      console.error("   Then call claimVesting() immediately after deployment\n");
    }

    if (error.code) {
      console.error(`   Error code: ${error.code}\n`);
    }

    process.exit(1);
  }
}

// ============================================================================
// 🎬 SCRIPT EXECUTION
// ============================================================================

console.log("\n🚀 DEXArb DataCoin Creation Script");
console.log("For ETHOnline 2025 - Lighthouse Prize Track\n");

createDataCoin()
  .then(() => {
    console.log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
    console.log("✅ SCRIPT COMPLETED SUCCESSFULLY!");
    console.log("   Ready for async hackathon judging!");
    console.log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n");
    process.exit(0);
  })
  .catch((error) => {
    console.error("\n💥 Script failed:", error.message);
    process.exit(1);
  });
