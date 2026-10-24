"""Disabled boundary until a specific official municipal export contract is verified."""
from .security import fail


def capabilities():
    return {'provider':'TCE_MG_SICOM','state':'blocked','connector_verified':False,'can_ingest':False,
        'resource_url':None,'schema_version':None,'municipal_identity_mapping':None,
        'records_imported':None,'municipal_purchase_completeness':None,
        'reason_codes':['OFFICIAL_EXPORT_NOT_VERIFIED','SCHEMA_NOT_VERIFIED','IDENTITY_MAPPING_NOT_VERIFIED'],
        'message':'Ainda falta validar um arquivo oficial, seu esquema e a identificação dos municípios.'}


def ingest(ctx,request=None):
    ctx.require('sources.sync')
    # Caller-supplied "verified" flags never authorize a connector. No opening
    # of files, HTTP request, staging, facts or coverage writes before this gate.
    fail(409,'Ainda não há um contrato de dados oficial validado para importar esta fonte.','TCE_SOURCE_UNVERIFIED')
