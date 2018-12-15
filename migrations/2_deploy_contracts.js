var contract = artifacts.require("./LearningContract.sol");

module.exports = function(deployer) {
  deployer.deploy(contract);
}
