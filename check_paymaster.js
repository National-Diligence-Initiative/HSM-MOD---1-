import { ethers } from "hardhat";
import { EntryPoint__factory, VerifyingPaymaster__factory } 
  from "@account-abstraction/contracts";

async function main() {
  const [deployer] = await ethers.getSigners();
  console.log("Deploying from:", deployer.address);

  const entryPoint = await new EntryPoint__factory(deployer).deploy();
  const paymaster = await new VerifyingPaymaster__factory(deployer)
      .deploy(await entryPoint.getAddress(), deployer.address);

  console.log("EntryPoint:", await entryPoint.getAddress());
  console.log("Paymaster:", await paymaster.getAddress());
}

main().catch(console.error);
