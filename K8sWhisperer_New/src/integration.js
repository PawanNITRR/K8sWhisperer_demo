import * as StellarSdk from '@stellar/stellar-sdk';

const { Keypair, TransactionBuilder, Operation, rpc, BASE_FEE, nativeToScVal } = StellarSdk;

/**
 * Stellar / Soroban logging — off unless VITE_ENABLE_STELLAR=true and keys are set.
 * Default: no-op so the dashboard works without Web3 configuration.
 */
export const logIncidentToBlockchain = async (incidentData) => {
  const enabled =
    typeof import.meta !== 'undefined' && import.meta.env?.VITE_ENABLE_STELLAR === 'true';
  if (!enabled) {
    return null;
  }

  const stellarSecret =
    (typeof import.meta !== 'undefined' && import.meta.env?.VITE_STELLAR_SECRET) || '';
  const contractId =
    (typeof import.meta !== 'undefined' && import.meta.env?.VITE_STELLAR_CONTRACT_ID) || '';
  if (!stellarSecret || !contractId) {
    console.info('Stellar enabled but VITE_STELLAR_SECRET / VITE_STELLAR_CONTRACT_ID missing.');
    return null;
  }

  try {
    const server = new rpc.Server('https://soroban-testnet.stellar.org');
    const networkPassphrase = 'Test SDF Network ; September 2015';

    const sourceKeypair = Keypair.fromSecret(stellarSecret);
    const account = await server.getAccount(sourceKeypair.publicKey());

    let tx = new TransactionBuilder(account, {
      fee: BASE_FEE,
      networkPassphrase,
    })
      .addOperation(
        Operation.invokeHostFunction({
          func: 'record_incident',
          args: [
            nativeToScVal(incidentData?.resource ?? ''),
            nativeToScVal(incidentData?.anomaly_type ?? ''),
            nativeToScVal(incidentData?.action ?? ''),
            nativeToScVal(incidentData?.explanation ?? ''),
          ],
          contractId,
        })
      )
      .setTimeout(30)
      .build();

    const simulation = await server.simulateTransaction(tx);
    tx = rpc.assembleTransaction(tx, simulation);
    tx.sign(sourceKeypair);
    const result = await server.sendTransaction(tx);

    if (result.status !== 'PENDING' && result.status !== 'SUCCESS') {
      throw new Error('Transaction failed during submission');
    }

    return result.hash;
  } catch (error) {
    console.warn('Stellar integration skipped:', error?.message || error);
    return null;
  }
};
