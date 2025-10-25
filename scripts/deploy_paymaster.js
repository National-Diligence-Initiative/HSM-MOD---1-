const hre = require("hardhat");

async function main() {
  const [deployer] = await hre.ethers.getSigners();

  console.log("Deploying with:", deployer.address);

  const HSMToken = await hre.ethers.getContractFactory("HSMToken");
  const token = await HSMToken.deploy();
  await token.waitForDeployment();
  console.log("HSMToken deployed at:", token.target);

  const Paymaster = await hre.ethers.getContractFactory("HSMTokenPaymaster");
  const paymaster = await Paymaster.deploy(
    "0xEntryPointAddressHere",
    token.target,
    10_000  // example: 10k HSM = 1 ETH gas
  );
  await paymaster.waitForDeployment();
  console.log("Paymaster deployed at:", paymaster.target);
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});

