/**
 * Deploy DataCoin Faucet for Async Hackathon
 * 
 * This script:
 * 1. Compiles and deploys the faucet contract
 * 2. Grants MINTER_ROLE to the faucet
 * 3. Verifies the setup
 */

const { ethers } = require("ethers");
const fs = require("fs");
const path = require("path");
require("dotenv").config();

const DatacoinABI = require("./abi/DataCoin.js");

// Configuration
const DATACOIN_ADDRESS = "0x8d302FfB73134235EBaD1B9Cd9C202d14f906FeC";
const CHAIN_NAME = "sepolia";
const RPC_URL = "https://ethereum-sepolia-rpc.publicnode.com";

// Faucet contract bytecode and ABI (will be generated)
const FAUCET_ABI = [
  "constructor(address _dataCoin)",
  "function claimTokens() external",
  "function hasClaimed(address account) external view returns (bool)",
  "function getClaimStatus(address account) external view returns (bool hasClaimed, uint256 amountClaimed, uint256 lastClaim, uint256 timeUntilNext)",
  "function CLAIM_AMOUNT() external view returns (uint256)",
  "function dataCoin() external view returns (address)",
  "event TokensClaimed(address indexed claimer, uint256 amount, uint256 timestamp)"
];

// Compile Solidity contract using solc
async function compileFaucetContract() {
  console.log("📦 Compiling faucet contract...\n");
  
  const solc = require("solc");
  const contractPath = path.join(__dirname, "..", "contracts", "DataCoinFaucet.sol");
  const source = fs.readFileSync(contractPath, "utf8");
  
  const input = {
    language: "Solidity",
    sources: {
      "DataCoinFaucet.sol": {
        content: source,
      },
    },
    settings: {
      optimizer: {
        enabled: true,
        runs: 200,
      },
      outputSelection: {
        "*": {
          "*": ["abi", "evm.bytecode"],
        },
      },
    },
  };
  
  const output = JSON.parse(solc.compile(JSON.stringify(input)));
  
  if (output.errors) {
    const errors = output.errors.filter(e => e.severity === "error");
    if (errors.length > 0) {
      console.error("❌ Compilation errors:");
      errors.forEach(e => console.error(e.formattedMessage));
      process.exit(1);
    }
  }
  
  const contract = output.contracts["DataCoinFaucet.sol"]["DataCoinFaucet"];
  console.log("✅ Contract compiled successfully\n");
  
  return {
    abi: contract.abi,
    bytecode: contract.evm.bytecode.object,
  };
}

async function deployFaucet() {
  console.log("🚀 Deploying DataCoin Faucet for Async Hackathon\n");
  console.log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n");
  
  try {
    // Compile contract
    const { abi, bytecode } = await compileFaucetContract();
    
    // Setup provider and wallet
    console.log("🔗 Connecting to Sepolia...\n");
    const provider = new ethers.JsonRpcProvider(RPC_URL);
    const wallet = new ethers.Wallet(process.env.PRIVATE_KEY, provider);
    console.log(`✅ Connected as: ${wallet.address}\n`);
    
    // Deploy faucet contract
    console.log("🏗️  Deploying faucet contract...\n");
    const FaucetFactory = new ethers.ContractFactory(abi, bytecode, wallet);
    const faucet = await FaucetFactory.deploy(DATACOIN_ADDRESS);
    await faucet.waitForDeployment();
    
    const faucetAddress = await faucet.getAddress();
    console.log(`✅ Faucet deployed at: ${faucetAddress}\n`);
    
    // Connect to DataCoin
    const dataCoin = new ethers.Contract(DATACOIN_ADDRESS, DatacoinABI, wallet);
    
    // Grant MINTER_ROLE to faucet
    console.log("🔑 Granting MINTER_ROLE to faucet...\n");
    const MINTER_ROLE = ethers.keccak256(ethers.toUtf8Bytes("MINTER_ROLE"));
    const grantTx = await dataCoin.grantRole(MINTER_ROLE, faucetAddress);
    await grantTx.wait();
    console.log(`✅ MINTER_ROLE granted (tx: ${grantTx.hash})\n`);
    
    // Verify setup
    console.log("🔍 Verifying setup...\n");
    const hasRole = await dataCoin.hasRole(MINTER_ROLE, faucetAddress);
    const claimAmount = await faucet.CLAIM_AMOUNT();
    
    if (!hasRole) {
      throw new Error("Failed to grant MINTER_ROLE to faucet");
    }
    
    console.log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n");
    console.log("🎉 FAUCET DEPLOYED SUCCESSFULLY!\n");
    console.log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n");
    
    console.log("📋 Deployment Details:\n");
    console.log(`   🪙  DataCoin: ${DATACOIN_ADDRESS}`);
    console.log(`   🚰  Faucet: ${faucetAddress}`);
    console.log(`   💧  Claim Amount: ${ethers.formatUnits(claimAmount, 18)} DADC`);
    console.log(`   🔑  MINTER_ROLE: Granted ✅`);
    console.log(`   🌐  Network: ${CHAIN_NAME}\n`);
    
    console.log("🔗 Etherscan Links:\n");
    console.log(`   Faucet: https://sepolia.etherscan.io/address/${faucetAddress}`);
    console.log(`   DataCoin: https://sepolia.etherscan.io/address/${DATACOIN_ADDRESS}\n`);
    
    console.log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n");
    console.log("📝 FOR JUDGES (Add to README):\n");
    console.log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n");
    console.log("## 🪙 Get DADC Tokens (For Judges)\n");
    console.log("### Option 1: Use Etherscan (Easiest)\n");
    console.log(`1. Go to: https://sepolia.etherscan.io/address/${faucetAddress}#writeContract`);
    console.log("2. Click 'Connect to Web3'");
    console.log("3. Connect your wallet");
    console.log("4. Click 'claimTokens'");
    console.log("5. Click 'Write' and confirm transaction");
    console.log("6. You'll receive 100 DADC tokens!\n");
    console.log("### Option 2: Use ethers.js\n");
    console.log("```javascript");
    console.log(`const faucet = new ethers.Contract("${faucetAddress}", [...], signer);`);
    console.log("await faucet.claimTokens();");
    console.log("```\n");
    console.log("### Check Your Balance\n");
    console.log("```javascript");
    console.log(`const dataCoin = new ethers.Contract("${DATACOIN_ADDRESS}", [...], provider);`);
    console.log("const balance = await dataCoin.balanceOf(yourAddress);");
    console.log("```\n");
    
    // Save deployment info
    const deploymentInfo = {
      network: CHAIN_NAME,
      timestamp: new Date().toISOString(),
      dataCoinAddress: DATACOIN_ADDRESS,
      faucetAddress: faucetAddress,
      claimAmount: ethers.formatUnits(claimAmount, 18),
      grantRoleTx: grantTx.hash,
      faucetABI: abi,
    };
    
    fs.writeFileSync(
      path.join(__dirname, "faucet-deployment.json"),
      JSON.stringify(deploymentInfo, null, 2)
    );
    
    console.log("💾 Deployment info saved to: scripts/faucet-deployment.json\n");
    console.log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n");
    
    return { faucetAddress, deploymentInfo };
    
  } catch (error) {
    console.error("\n❌ Error deploying faucet:");
    console.error(error.message);
    if (error.code) {
      console.error(`Error code: ${error.code}`);
    }
    process.exit(1);
  }
}

// Execute
deployFaucet()
  .then(() => {
    console.log("✅ All done! Judges can now claim tokens autonomously.\n");
    process.exit(0);
  })
  .catch((error) => {
    console.error("\n❌ Script failed:", error.message);
    process.exit(1);
  });
