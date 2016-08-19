var config = {};

config.host = "REPLACE THIS WITh YOUR HOST";

config.privateKey = new Buffer("-----BEGIN RSA PRIVATE KEY-----\n"+
	"MIIEowIBAAKCAQEApLNWNpwMw3ZWF11zMqxPqC6ylUcjC8X5rez1x30jOrXhQRfQ\n"+
	"xNlczVcQc7LuLkDWqY0ZQvCCzLF4G7qPmhYAABa6NfTPAENXQF+KKYplWpgKepCG\n"+
	"REPLACE this string block YOUR private key"+
	"cAthAoGBAKpXtEs5qlnaKTvl9kDbvAzzpCh9Ss5BsP41dbKJpE31FJgxGzdX+aDE\n"+
	"Z4GIT2tOO32DRWVvP7kJn8pz4dSA7L7PahNBi/b7n/kx6aCApk1KphVGLMYBlXMS\n"+
	"T5ry6RQapUZghptGvnMxEPxvIJLwe5deNCs4bX33QcnpCTkjVpxn\n"+
	"-----END RSA PRIVATE KEY-----\n");

config.certificate = new Buffer("-----BEGIN CERTIFICATE-----\n"+
	"MIIDWjCCAkKgAwIBAgIVAPMznG4C7qWdIHcPZauNDhZxB4Q6MA0GCSqGSIb3DQEB\n"+
	"CwUAME0xSzBJBgNVBAsMQkFtYXpvbiBXZWIgU2VydmljZXMgTz1BbWF6b24uY29t\n"+
	"REPLACE this string block YOUR certificate"+
	"4CNHkwK08nNJqQEoFjz/8DQ1Y7Onv0Ivyxg1tHlQNCPNKWPSRNhLTi1SliZh+fsZ\n"+
	"oBPPldZgsVFECKkIqH212Sf0LkzpcO5yzkS8jRsKP/oYsp/u1srCtB/xf+RQVa0v\n"+
	"YRHbeVhlYmRXBRJRFv9GfblWuRbOk3Yoa/yQRpNWBOjsa/3PNqPgnkHbC6EIHg==\n"+
	"-----END CERTIFICATE-----\n");


/**
 * Standard rootCA for everyone to use
 */
config.rootCA = new Buffer("-----BEGIN CERTIFICATE-----\n"+
	"MIIE0zCCA7ugAwIBAgIQGNrRniZ96LtKIVjNzGs7SjANBgkqhkiG9w0BAQUFADCB\n"+
	"yjELMAkGA1UEBhMCVVMxFzAVBgNVBAoTDlZlcmlTaWduLCBJbmMuMR8wHQYDVQQL\n"+
	"ExZWZXJpU2lnbiBUcnVzdCBOZXR3b3JrMTowOAYDVQQLEzEoYykgMjAwNiBWZXJp\n"+
	"U2lnbiwgSW5jLiAtIEZvciBhdXRob3JpemVkIHVzZSBvbmx5MUUwQwYDVQQDEzxW\n"+
	"ZXJpU2lnbiBDbGFzcyAzIFB1YmxpYyBQcmltYXJ5IENlcnRpZmljYXRpb24gQXV0\n"+
	"aG9yaXR5IC0gRzUwHhcNMDYxMTA4MDAwMDAwWhcNMzYwNzE2MjM1OTU5WjCByjEL\n"+
	"MAkGA1UEBhMCVVMxFzAVBgNVBAoTDlZlcmlTaWduLCBJbmMuMR8wHQYDVQQLExZW\n"+
	"ZXJpU2lnbiBUcnVzdCBOZXR3b3JrMTowOAYDVQQLEzEoYykgMjAwNiBWZXJpU2ln\n"+
	"biwgSW5jLiAtIEZvciBhdXRob3JpemVkIHVzZSBvbmx5MUUwQwYDVQQDEzxWZXJp\n"+
	"U2lnbiBDbGFzcyAzIFB1YmxpYyBQcmltYXJ5IENlcnRpZmljYXRpb24gQXV0aG9y\n"+
	"aXR5IC0gRzUwggEiMA0GCSqGSIb3DQEBAQUAA4IBDwAwggEKAoIBAQCvJAgIKXo1\n"+
	"nmAMqudLO07cfLw8RRy7K+D+KQL5VwijZIUVJ/XxrcgxiV0i6CqqpkKzj/i5Vbex\n"+
	"t0uz/o9+B1fs70PbZmIVYc9gDaTY3vjgw2IIPVQT60nKWVSFJuUrjxuf6/WhkcIz\n"+
	"SdhDY2pSS9KP6HBRTdGJaXvHcPaz3BJ023tdS1bTlr8Vd6Gw9KIl8q8ckmcY5fQG\n"+
	"BO+QueQA5N06tRn/Arr0PO7gi+s3i+z016zy9vA9r911kTMZHRxAy3QkGSGT2RT+\n"+
	"rCpSx4/VBEnkjWNHiDxpg8v+R70rfk/Fla4OndTRQ8Bnc+MUCH7lP59zuDMKz10/\n"+
	"NIeWiu5T6CUVAgMBAAGjgbIwga8wDwYDVR0TAQH/BAUwAwEB/zAOBgNVHQ8BAf8E\n"+
	"BAMCAQYwbQYIKwYBBQUHAQwEYTBfoV2gWzBZMFcwVRYJaW1hZ2UvZ2lmMCEwHzAH\n"+
	"BgUrDgMCGgQUj+XTGoasjY5rw8+AatRIGCx7GS4wJRYjaHR0cDovL2xvZ28udmVy\n"+
	"aXNpZ24uY29tL3ZzbG9nby5naWYwHQYDVR0OBBYEFH/TZafC3ey78DAJ80M5+gKv\n"+
	"MzEzMA0GCSqGSIb3DQEBBQUAA4IBAQCTJEowX2LP2BqYLz3q3JktvXf2pXkiOOzE\n"+
	"p6B4Eq1iDkVwZMXnl2YtmAl+X6/WzChl8gGqCBpH3vn5fJJaCGkgDdk+bW48DW7Y\n"+
	"5gaRQBi5+MHt39tBquCWIMnNZBU4gcmU7qKEKQsTb47bDN0lAtukixlE0kF6BWlK\n"+
	"WE9gyn6CagsCqiUXObXbf+eEZSqVir2G3l6BFoMtEMze/aiCKm0oHw0LxOXnGiYZ\n"+
	"4fQRbxC1lfznQgUy286dUV4otp6F01vvpX1FQHKOtw5rDgb7MzVIcbidJ4vEZV8N\n"+
	"hnacRHr2lVz2XTIIM6RUthg/aFzyQkqFOFSDX9HoLPKsEdao7WNq\n"+
	"-----END CERTIFICATE-----");



module.exports = config;