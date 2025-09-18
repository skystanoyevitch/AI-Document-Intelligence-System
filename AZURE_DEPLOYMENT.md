# Azure Deployment Configuration

## Setting Environment Variables in Azure App Service

After deploying your app to Azure App Service, you need to configure the environment variables securely:

### Method 1: Using Azure Portal

1. Navigate to your App Service in the Azure Portal
2. Go to **Settings** > **Environment variables**
3. Add the following Application Settings:

   | Name | Value |
   |------|-------|
   | `AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT` | `https://eastus.api.cognitive.microsoft.com/` |
   | `AZURE_DOCUMENT_INTELLIGENCE_KEY` | `your_actual_key_here` |

4. Click **Apply** to save the settings
5. Restart your App Service

### Method 2: Using Azure CLI

```bash
# Set the environment variables
az webapp config appsettings set \
  --resource-group your-resource-group \
  --name your-app-name \
  --settings \
    AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT="https://eastus.api.cognitive.microsoft.com/" \
    AZURE_DOCUMENT_INTELLIGENCE_KEY="your_actual_key_here"
```

### Security Best Practice: Use Key Vault (Recommended)

For production environments, store your secrets in Azure Key Vault:

1. Create an Azure Key Vault
2. Add your Document Intelligence key as a secret
3. Enable Managed Identity for your App Service
4. Grant the App Service access to Key Vault
5. Reference the secret in App Settings using Key Vault syntax:
   ```
   @Microsoft.KeyVault(SecretUri=https://your-keyvault.vault.azure.net/secrets/document-intelligence-key/)
   ```

## Deployment Checklist

- [ ] Remove .env from version control (already done)
- [ ] Set environment variables in Azure App Service
- [ ] Rebuild and deploy the frontend
- [ ] Test the application in production
- [ ] Monitor logs for any issues

## Testing the Fix

1. Deploy your updated code to Azure
2. Visit your app's domain
3. Try uploading a receipt image
4. Check that the API calls are working (Network tab in browser dev tools)
5. Verify receipt analysis results are displayed

If you still see a blank page:
1. Check browser console for JavaScript errors
2. Check Azure App Service logs
3. Verify environment variables are set correctly
4. Ensure the build folder contains the updated frontend files