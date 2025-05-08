from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
from datetime import datetime
import io
from typing import Optional
from pydantic import BaseModel

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class StoreConfig(BaseModel):
    gestorEntityId: int
    gestorNome: str
    storeNome: str
    numeroRegistroJunta: Optional[str] = None
    gestorId: Optional[int] = None
    gestorLogo: str
    storeUri: str
    gestorContactEmail: str
    gestorTabela: int
    leiloeiroEntityId: Optional[str] = None
    isencaoDeTaxa: Optional[str] = 'N'
    origemLoja: str

def get_sql_template(origem_loja: str) -> str:
    templates = {
        "lw": """
DECLARE
    gestorPortal NUMBER;
    usuarioIntegracao1 VARCHAR2(4000);
    usuarioIntegracao1PerfilId NUMBER;
    usuarioIntegracao2 VARCHAR2(4000);
    usuarioIntegracao2PerfilId NUMBER;
    gestorId NUMBER;
    gestorEntityId NUMBER;
    gestorNome VARCHAR2(4000);
    numeroRegistroJunta VARCHAR2(4000);
    storeId NUMBER;
    storeNome VARCHAR2(4000);
    gestorLogo VARCHAR2(4000);
    storeUri VARCHAR2(4000);
    gestorContactEmail VARCHAR2(4000);
    gestorTabela NUMBER;
    codCondicaoComercial NUMBER;
    isencaoDeTaxa VARCHAR2(1);
    v_exists NUMBER;
BEGIN
    gestorPortal := 2;
    usuarioIntegracao1 := 'nws.integracao';
    usuarioIntegracao2 := 'nws.integracao2';
    
    -- INICIO DADOS CUSTOMIZAVEIS
    gestorEntityId := {gestorEntityId};
    gestorNome := '{gestorNome}';
    storeNome := '{storeNome}';
    numeroRegistroJunta := '{numeroRegistroJunta}';
    SELECT NVL(MAX(GESTOR_ID), 0) + 1 INTO gestorId FROM GESTOR;
    gestorLogo := '{gestorLogo}';
    storeUri := '{storeUri}';
    gestorContactEmail := '{gestorContactEmail}';
    gestorTabela := {gestorTabela};
    isencaoDeTaxa := '{isencaoDeTaxa}';
    -- FIM DADOS CUSTOMIZAVEIS

    -- ETAPA 1 - CRIAR GESTOR
    -- Atribuir papel de gestor para entity
    SELECT COUNT(*) INTO v_exists FROM REL_ROLE_ENTITY WHERE ENTITY_ID = gestorEntityId AND ROLE_ID = 40;
    IF v_exists = 0 THEN
        INSERT INTO REL_ROLE_ENTITY (ENTITY_ID, ROLE_ID)
        VALUES (gestorEntityId, 40);
    END IF;

    SELECT COUNT(*) INTO v_exists FROM INTER_ENTITY WHERE ENTITY_ID = gestorEntityId AND ENTITY_PARENT_ID = gestorEntityId AND ROLE_ID = 40;
    IF v_exists = 0 THEN
        INSERT INTO INTER_ENTITY (ENTITY_ID, ENTITY_PARENT_ID, ROLE_ID)
        VALUES (gestorEntityId, gestorEntityId, 40);
    END IF;

    -- Cadastrar gestor 
    INSERT INTO GESTOR (GESTOR_ID, GESTOR, ENTITY_ID, GESTOR_TITLE, GESTOR_DESC, GESTOR_INATIVO, EREG_PORTAL_ID)
    VALUES (gestorId, gestorNome, gestorEntityId, gestorNome, gestorNome, 'F', gestorPortal);
    --desc gestor;
        
    INSERT INTO GESTOR_SETTINGS (GESTOR_ID,SHOW_ITENS_PORCENTAGEM,COUNTRY_CODE,COD_ERP_SYSTEM,ERP_KEY,AUTO_SALE_START,SYSTEM_CONTACT_EMAIL,AUTO_SALE_GENERATE,GESTOR_CONTACT_EMAIL,COD_PROJETO_LEILAO, PLATFORM_LICENSOR_ID) 
    values (gestorId,'2,3','1',2,'CORPORE_RM','01/01/1900','transaction-team@superbid.net','T',gestorContactEmail,165064, 3);

    INSERT INTO GESTOR_GEO_APPROVAL_DEFAULT (EREF_COUNTRY_CODE, GESTOR_ID) VALUES (1,gestorId);

    -- Projeto Comercial (61922 - Superbid Webservices)
    INSERT INTO COMMERCIAL_PROJECT (COMMERCIAL_PROJECT_DESC,COMMERCIAL_PROJECT_STATUS_ID,OWNER_ID,YOUR_REFERENCE,CREATED_AT,UPDATED_AT,CLOSE_AT,GESTOR_ID,ECONOMIC_GROUP_ID)
        values ('PROJETO PADRAO','1','61922','',SYSDATE,null,SYSDATE,gestorId,null);

    -- Dar acesso as APIS ao usuario do administrativo ( GATE , Plataforma Leiloes, etc.. )
    SELECT PERFIL_ID INTO usuarioIntegracao1PerfilId FROM PERFIL WHERE ENTITY_ID IN (SELECT ENTITY_ID FROM LOGIN WHERE LOGIN_NAME = usuarioIntegracao1) AND EREG_PORTAL_ID = gestorPortal;

    INSERT INTO PERFIL_PERMISSAO (PERFIL_ID, MODULO_ID, CREATION_DATE, PAPEL_ID, GESTOR_ID)  VALUES (usuarioIntegracao1PerfilId,'PRG0002',SYSDATE,35,gestorId); -- Operador do Pregão
    INSERT INTO PERFIL_PERMISSAO (PERFIL_ID, MODULO_ID, CREATION_DATE, PAPEL_ID, GESTOR_ID)  VALUES (usuarioIntegracao1PerfilId,'CDV0002',SYSDATE,36,gestorId); -- Operador Condicao de Venda
    INSERT INTO PERFIL_PERMISSAO (PERFIL_ID, MODULO_ID, CREATION_DATE, PAPEL_ID, GESTOR_ID)  VALUES (usuarioIntegracao1PerfilId,'LOT0002',SYSDATE,11,gestorId); -- Operador do modulo loteamento Superbid
    INSERT INTO PERFIL_PERMISSAO (PERFIL_ID, MODULO_ID, CREATION_DATE, PAPEL_ID, GESTOR_ID)  VALUES (usuarioIntegracao1PerfilId,'CCF',SYSDATE,71,gestorId); -- Adminstrador do Modulo
    INSERT INTO PERFIL_PERMISSAO (PERFIL_ID, MODULO_ID, CREATION_DATE, PAPEL_ID, GESTOR_ID)  VALUES (usuarioIntegracao1PerfilId,'CPC',SYSDATE,106,gestorId); -- Administrador do Módulo
    INSERT INTO PERFIL_PERMISSAO (PERFIL_ID, MODULO_ID, CREATION_DATE, PAPEL_ID, GESTOR_ID)  VALUES (usuarioIntegracao1PerfilId,'CDA',SYSDATE,111,gestorId); -- Adminstrador CDA - GATE 1.0

    -- Dar acesso as APIS ao usuario do administrativo ( GATE , Plataforma Leiloes, etc.. )
    SELECT PERFIL_ID INTO usuarioIntegracao2PerfilId FROM PERFIL WHERE ENTITY_ID IN (SELECT ENTITY_ID FROM LOGIN WHERE LOGIN_NAME = usuarioIntegracao2) AND EREG_PORTAL_ID = gestorPortal;

    INSERT INTO PERFIL_PERMISSAO (PERFIL_ID, MODULO_ID, CREATION_DATE, PAPEL_ID, GESTOR_ID)  VALUES (usuarioIntegracao2PerfilId,'PRG0002',SYSDATE,35,gestorId); -- Operador do Pregão
    INSERT INTO PERFIL_PERMISSAO (PERFIL_ID, MODULO_ID, CREATION_DATE, PAPEL_ID, GESTOR_ID)  VALUES (usuarioIntegracao2PerfilId,'CDV0002',SYSDATE,36,gestorId); -- Operador Condicao de Venda
    INSERT INTO PERFIL_PERMISSAO (PERFIL_ID, MODULO_ID, CREATION_DATE, PAPEL_ID, GESTOR_ID)  VALUES (usuarioIntegracao2PerfilId,'LOT0002',SYSDATE,11,gestorId); -- Operador do modulo loteamento Superbid
    INSERT INTO PERFIL_PERMISSAO (PERFIL_ID, MODULO_ID, CREATION_DATE, PAPEL_ID, GESTOR_ID)  VALUES (usuarioIntegracao2PerfilId,'CCF',SYSDATE,71,gestorId); -- Adminstrador do Modulo
    INSERT INTO PERFIL_PERMISSAO (PERFIL_ID, MODULO_ID, CREATION_DATE, PAPEL_ID, GESTOR_ID)  VALUES (usuarioIntegracao2PerfilId,'CPC',SYSDATE,106,gestorId); -- Administrador do Módulo
    INSERT INTO PERFIL_PERMISSAO (PERFIL_ID, MODULO_ID, CREATION_DATE, PAPEL_ID, GESTOR_ID)  VALUES (usuarioIntegracao2PerfilId,'CDA',SYSDATE,111,gestorId); -- Adminstrador CDA - GATE 1.0

    -- SETUP TRANSACIONAL FINANCEIRO

    -- Forma de Pagamento
    INSERT INTO FL_FORMA_PAGAMENTO_GESTOR VALUES(gestorId,2); --Depósito
    INSERT INTO FL_FORMA_PAGAMENTO_GESTOR VALUES(gestorId,9); --S4Payments
    INSERT INTO FL_FORMA_PAGAMENTO_GESTOR VALUES(gestorId,11); --Guia de depósito Judicial

    -- Itens de Pagamento - 1º Split
    INSERT INTO FL_TIPO_ITEM_PAG_GESTOR(COD_GESTOR, COD_TIPO_ITEM_PAGAMENTO, DATA_CRIACAO, STATUS, ORDEM_BAIXA) VALUES(gestorId, 1, SYSDATE, 'T', 3); --Pagamento do lote
    INSERT INTO FL_TIPO_ITEM_PAG_GESTOR(COD_GESTOR, COD_TIPO_ITEM_PAGAMENTO, DATA_CRIACAO, STATUS, ORDEM_BAIXA) VALUES(gestorId, 2, SYSDATE, 'T', 1); --Comissão do leiloeiro
    INSERT INTO FL_TIPO_ITEM_PAG_GESTOR(COD_GESTOR, COD_TIPO_ITEM_PAGAMENTO, DATA_CRIACAO, STATUS, ORDEM_BAIXA) VALUES(gestorId, 5, SYSDATE, 'T', 2); --Encargos de Administração
    INSERT INTO FL_TIPO_ITEM_PAG_GESTOR(COD_GESTOR, COD_TIPO_ITEM_PAGAMENTO, DATA_CRIACAO, STATUS, ORDEM_BAIXA) VALUES(gestorId, 3, SYSDATE, 'T', 2); --Buyers

    -- Itens de Serviço - 2º Split

    IF isencaoDeTaxa != 'S' THEN

    INSERT INTO FL_TIPO_ITEM_SERV_GESTOR(COD_GESTOR, COD_TIPO_ITEM_SERVICO, STATUS) VALUES(gestorId, 1, 'T'); --Vendedor
    INSERT INTO FL_TIPO_ITEM_SERV_GESTOR(COD_GESTOR, COD_TIPO_ITEM_SERVICO, STATUS) VALUES(gestorId, 2, 'T'); --Licenciamento
    INSERT INTO FL_TIPO_ITEM_SERV_GESTOR(COD_GESTOR, COD_TIPO_ITEM_SERVICO, STATUS) VALUES(gestorId, 3, 'T'); --Assessoria

    ELSE

    INSERT INTO FL_TIPO_ITEM_SERV_GESTOR(COD_GESTOR, COD_TIPO_ITEM_SERVICO, STATUS) VALUES(gestorId, 1, 'T'); --Vendedor
    INSERT INTO FL_TIPO_ITEM_SERV_GESTOR(COD_GESTOR, COD_TIPO_ITEM_SERVICO, STATUS) VALUES(gestorId, 3, 'T'); --Assessoria

    END IF;

    -- SETUP LOJA
    INSERT INTO SBINS.STORE (ID, NAME,CREATED_AT,UPDATED_AT,PORTAL_ID,VISIBLE_ON_PORTAL,HIGHLIGHT,LOGO_URI,DESCRIPTION,POSITION,EXTERNAL_LINK,VISIBLE_ON_PORTAL_BANNER,LAST_UPDATE_DATE,STORE_URI) 
    values ((SELECT MAX(ID)+1 FROM STORE),UPPER(storeNome),SYSDATE,SYSDATE,15,'T','T',gestorLogo,UPPER(storeNome),null,null,'T',SYSDATE,storeUri) RETURNING ID INTO storeId;

    INSERT INTO REL_STORE_EVENT_MANAGER ( STORE_ID, EVENT_MANAGER_ID ) VALUES ( storeId, gestorId );

    -- SETUP LEILOEIRO
    IF numeroRegistroJunta IS NOT NULL THEN
        SELECT COUNT(*) INTO v_exists FROM INTER_ENTITY WHERE ENTITY_ID = gestorEntityId AND ENTITY_PARENT_ID = gestorEntityId AND ROLE_ID = 11;
        IF v_exists = 0 THEN
        INSERT INTO INTER_ENTITY (ENTITY_ID, ENTITY_PARENT_ID, ROLE_ID)
        VALUES (gestorEntityId, gestorEntityId, 11);
        END IF;

        SELECT COUNT(*) INTO v_exists FROM DOCUMENT WHERE DOCUMENT_NUMBER = numeroRegistroJunta AND DOCUMENT_TYPE_ID = 6 AND ENTITY_ID = gestorEntityId;
        IF v_exists = 0 THEN
        INSERT INTO DOCUMENT (DOCUMENT_NUMBER, DOCUMENT_TYPE_ID, ENTITY_ID)
        VALUES (numeroRegistroJunta, 6, gestorEntityId);
        END IF;

        SELECT COUNT(*) INTO v_exists FROM REL_GESTOR_AUCTIONEER WHERE GESTOR_ID = gestorId AND ENTITY_ID = gestorEntityId;
        IF v_exists = 0 THEN
        INSERT INTO REL_GESTOR_AUCTIONEER (GESTOR_ID, ENTITY_ID)
        VALUES (gestorId, gestorEntityId);
        END IF;
    END IF;

    -- NOVO PERMISSIONAMENTO FINLEI
    INSERT INTO gestor_acesso (GESTOR_ID,GESTOR_ID_PAI) VALUES(gestorId,114);

    IF isencaoDeTaxa != 'S' THEN

    -- CRIAR CONDICAO DE PLATAFORMA
    insert into fl_ccvenda (COD_CONDICAO_COMERCIAL,DESC_CONDICAO_COMERCIAL,COD_TIPO_TRANSACAO,COD_GESTOR,COD_VENDEDOR,COD_EVENTO,COD_OFERTA,COD_FORMA_PAGAMENTO,COD_FAVORECIDO,DIAS_VENCIMENTO,INSTRUCAO_PAGAMENTO,DATA_CRIACAO,DATA_ATUALIZACAO,COD_STATUS,MIN_PORCENTAGEM_ENTRADA,MAX_QUANTIDADE_PARCELAS,AFTER_CASHOUT,COBRANCA_PLATAFORMA,DATA_EXPIRACAO,DIAS_CONDICIONAL,TIPO_FAVORECIDO)
    values ((SELECT MAX(COD_CONDICAO_COMERCIAL)+1 FROM fl_ccvenda),gestorId || ' ' || gestorNome || ' - TABELA ' || gestorTabela,1,gestorId,null,null,null,null,null,null,null,SYSDATE,SYSDATE,2,null,null,null,'T',null,null,null) RETURNING COD_CONDICAO_COMERCIAL INTO codCondicaoComercial;

    insert into fl_ccvenda_item (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO) values (codCondicaoComercial,2);

    insert into fl_ccvenda_split (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_TIPO_ITEM_SERVICO,COD_FAVORECIDO,COD_TIPO_COBRANCA,COD_BASE_CALCULO,PORCENTAGEM,VALOR,VALOR_MAXIMO)
    values (codCondicaoComercial,2,2,61922,3,1,null,null,null);

    ELSE

    insert into fl_ccvenda (COD_CONDICAO_COMERCIAL,DESC_CONDICAO_COMERCIAL,COD_TIPO_TRANSACAO,COD_GESTOR,COD_VENDEDOR,COD_EVENTO,COD_OFERTA,COD_FORMA_PAGAMENTO,COD_FAVORECIDO,DIAS_VENCIMENTO,INSTRUCAO_PAGAMENTO,DATA_CRIACAO,DATA_ATUALIZACAO,COD_STATUS,MIN_PORCENTAGEM_ENTRADA,MAX_QUANTIDADE_PARCELAS,AFTER_CASHOUT,COBRANCA_PLATAFORMA,DATA_EXPIRACAO,DIAS_CONDICIONAL,TIPO_FAVORECIDO)
    values ((SELECT MAX(COD_CONDICAO_COMERCIAL)+1 FROM fl_ccvenda),gestorId || ' ' || gestorNome || ' - TABELA ' || gestorTabela,1,gestorId,null,null,null,null,null,null,null,SYSDATE,SYSDATE,3,null,null,null,'T',null,null,null) RETURNING COD_CONDICAO_COMERCIAL INTO codCondicaoComercial;

    insert into fl_ccvenda_item (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO) values (codCondicaoComercial,2);

    insert into fl_ccvenda_split (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_TIPO_ITEM_SERVICO,COD_FAVORECIDO,COD_TIPO_COBRANCA,COD_BASE_CALCULO,PORCENTAGEM,VALOR,VALOR_MAXIMO)
    values (codCondicaoComercial,2,2,61922,3,1,null,null,null);

    END IF;

    -- INICIO TABELA 1
    IF gestorTabela = 1 THEN

        insert into fl_ccvenda_split_faixa (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_TIPO_ITEM_SERVICO,VALOR_INICIAL,VALOR_FINAL,PORCENTAGEM,VALOR)
            values (codCondicaoComercial,'2','2','3000,01','10000',null,'50');
        insert into fl_ccvenda_split_faixa (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_TIPO_ITEM_SERVICO,VALOR_INICIAL,VALOR_FINAL,PORCENTAGEM,VALOR)
            values (codCondicaoComercial,'2','2','10000,01','30000',null,'150');
        insert into fl_ccvenda_split_faixa (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_TIPO_ITEM_SERVICO,VALOR_INICIAL,VALOR_FINAL,PORCENTAGEM,VALOR)
            values (codCondicaoComercial,'2','2','30000,01','100000',null,'250');
        insert into fl_ccvenda_split_faixa (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_TIPO_ITEM_SERVICO,VALOR_INICIAL,VALOR_FINAL,PORCENTAGEM,VALOR)
            values (codCondicaoComercial,'2','2','100000,01','999999999999',null,'350');

    END IF;

    -- FIM TABELA 1

    -- INICIO TABELA 2
    IF gestorTabela = 2 THEN

        insert into fl_ccvenda_split_faixa (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_TIPO_ITEM_SERVICO,VALOR_INICIAL,VALOR_FINAL,PORCENTAGEM,VALOR)
            values (codCondicaoComercial,'2','2','3000,01','10000',null,'50');
        insert into fl_ccvenda_split_faixa (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_TIPO_ITEM_SERVICO,VALOR_INICIAL,VALOR_FINAL,PORCENTAGEM,VALOR)
            values (codCondicaoComercial,'2','2','10000,01','30000',null,'150');
        insert into fl_ccvenda_split_faixa (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_TIPO_ITEM_SERVICO,VALOR_INICIAL,VALOR_FINAL,PORCENTAGEM,VALOR)
            values (codCondicaoComercial,'2','2','30000,01','100000',null,'350');
        insert into fl_ccvenda_split_faixa (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_TIPO_ITEM_SERVICO,VALOR_INICIAL,VALOR_FINAL,PORCENTAGEM,VALOR)
            values (codCondicaoComercial,'2','2','100000,01','300000',null,'600');
        insert into fl_ccvenda_split_faixa (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_TIPO_ITEM_SERVICO,VALOR_INICIAL,VALOR_FINAL,PORCENTAGEM,VALOR)
            values (codCondicaoComercial,'2','2','300000,01','999999999999',null,'1000');

    END IF;

    -- FIM TABELA 2

    -- INICIO TABELA 3
    IF gestorTabela = 3 THEN

        insert into fl_ccvenda_split_faixa (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_TIPO_ITEM_SERVICO,VALOR_INICIAL,VALOR_FINAL,PORCENTAGEM,VALOR)
            values (codCondicaoComercial,'2','2','0','10000',null,'50');
        insert into fl_ccvenda_split_faixa (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_TIPO_ITEM_SERVICO,VALOR_INICIAL,VALOR_FINAL,PORCENTAGEM,VALOR)
            values (codCondicaoComercial,'2','2','10000,01','30000',null,'150');
        insert into fl_ccvenda_split_faixa (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_TIPO_ITEM_SERVICO,VALOR_INICIAL,VALOR_FINAL,PORCENTAGEM,VALOR)
            values (codCondicaoComercial,'2','2','30000,01','100000',null,'350');
        insert into fl_ccvenda_split_faixa (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_TIPO_ITEM_SERVICO,VALOR_INICIAL,VALOR_FINAL,PORCENTAGEM,VALOR)
            values (codCondicaoComercial,'2','2','100000,01','300000',null,'600');
        insert into fl_ccvenda_split_faixa (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_TIPO_ITEM_SERVICO,VALOR_INICIAL,VALOR_FINAL,PORCENTAGEM,VALOR)
            values (codCondicaoComercial,'2','2','300000,01','999999999999',null,'1000');

    END IF;

    -- FIM TABELA 3

    -- INICIO TABELA 4
    IF gestorTabela = 4 THEN

        insert into fl_ccvenda_split_faixa (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_TIPO_ITEM_SERVICO,VALOR_INICIAL,VALOR_FINAL,PORCENTAGEM,VALOR)
            values (codCondicaoComercial,'2','2','0','10000',null,'10');
        insert into fl_ccvenda_split_faixa (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_TIPO_ITEM_SERVICO,VALOR_INICIAL,VALOR_FINAL,PORCENTAGEM,VALOR)
            values (codCondicaoComercial,'2','2','10000,01','30000',null,'150');
        insert into fl_ccvenda_split_faixa (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_TIPO_ITEM_SERVICO,VALOR_INICIAL,VALOR_FINAL,PORCENTAGEM,VALOR)
            values (codCondicaoComercial,'2','2','30000,01','100000',null,'350');
        insert into fl_ccvenda_split_faixa (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_TIPO_ITEM_SERVICO,VALOR_INICIAL,VALOR_FINAL,PORCENTAGEM,VALOR)
            values (codCondicaoComercial,'2','2','100000,01','300000',null,'600');
        insert into fl_ccvenda_split_faixa (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_TIPO_ITEM_SERVICO,VALOR_INICIAL,VALOR_FINAL,PORCENTAGEM,VALOR)
            values (codCondicaoComercial,'2','2','300000,01','999999999999',null,'1000');

    END IF;

    -- FIM TABELA 4

    END;
    /
""",
        "canal_do_campo": """
DECLARE
    gestorPortal NUMBER;
    usuarioIntegracao1 VARCHAR2(4000);
    usuarioIntegracao1PerfilId NUMBER;
    usuarioIntegracao2 VARCHAR2(4000);
    usuarioIntegracao2PerfilId NUMBER;
    gestorId NUMBER;
    gestorEntityId NUMBER;
    gestorNome VARCHAR2(4000);
    numeroRegistroJunta VARCHAR2(4000);
    storeId NUMBER;
    storeNome VARCHAR2(4000);
    gestorLogo VARCHAR2(4000);
    storeUri VARCHAR2(4000);
    gestorContactEmail VARCHAR2(4000);
    gestorTabela NUMBER;
    codCondicaoComercial NUMBER;
    isencaoDeTaxa VARCHAR2(1);
    v_exists NUMBER;
BEGIN
    gestorPortal := 2;
    usuarioIntegracao1 := 'nws.integracao';
    usuarioIntegracao2 := 'nws.integracao2';
    
    -- INICIO DADOS CUSTOMIZAVEIS
    gestorEntityId := {gestorEntityId};
    gestorNome := '{gestorNome}';
    storeNome := '{storeNome}';
    numeroRegistroJunta := '{numeroRegistroJunta}';
    gestorId := {gestorId};
    gestorLogo := '{gestorLogo}';
    storeUri := '{storeUri}';
    gestorContactEmail := '{gestorContactEmail}';
    gestorTabela := {gestorTabela};
    -- FIM DADOS CUSTOMIZAVEIS
    -- ETAPA 1 - CRIAR GESTOR

    -- Atribuir papel de gestor para entity
    SELECT COUNT(*) INTO v_exists FROM REL_ROLE_ENTITY WHERE ENTITY_ID = gestorEntityId AND ROLE_ID = 40;
    IF v_exists = 0 THEN
        INSERT INTO REL_ROLE_ENTITY (ENTITY_ID, ROLE_ID)
        VALUES (gestorEntityId, 40);
    END IF;

    SELECT COUNT(*) INTO v_exists FROM INTER_ENTITY WHERE ENTITY_ID = gestorEntityId AND ENTITY_PARENT_ID = gestorEntityId AND ROLE_ID = 40;
    IF v_exists = 0 THEN
        INSERT INTO INTER_ENTITY (ENTITY_ID, ENTITY_PARENT_ID, ROLE_ID)
        VALUES (gestorEntityId, gestorEntityId, 40);
    END IF;

    -- Cadastrar gestor 
    INSERT INTO GESTOR (GESTOR_ID, GESTOR, ENTITY_ID, GESTOR_TITLE, GESTOR_DESC, GESTOR_INATIVO, EREG_PORTAL_ID)
    VALUES (gestorId, gestorNome, gestorEntityId, gestorNome, gestorNome, 'F', gestorPortal);
    --desc gestor;
        
    INSERT INTO GESTOR_SETTINGS (GESTOR_ID,SHOW_ITENS_PORCENTAGEM,COUNTRY_CODE,COD_ERP_SYSTEM,ERP_KEY,AUTO_SALE_START,SYSTEM_CONTACT_EMAIL,AUTO_SALE_GENERATE,GESTOR_CONTACT_EMAIL) 
    values (gestorId,'2,3','1',2,'CORPORE_RM','01/01/1900','transaction-team@superbid.net','T',gestorContactEmail);

    INSERT INTO GESTOR_GEO_APPROVAL_DEFAULT (EREF_COUNTRY_CODE, GESTOR_ID) VALUES (1,gestorId);

    -- Projeto Comercial (61922 - Superbid Webservices)
    INSERT INTO COMMERCIAL_PROJECT (COMMERCIAL_PROJECT_DESC,COMMERCIAL_PROJECT_STATUS_ID,OWNER_ID,YOUR_REFERENCE,CREATED_AT,UPDATED_AT,CLOSE_AT,GESTOR_ID,ECONOMIC_GROUP_ID)
        values ('PROJETO PADRAO','1','61922','',SYSDATE,null,SYSDATE,gestorId,null);

    -- Dar acesso as APIS ao usuario do administrativo ( GATE , Plataforma Leiloes, etc.. )
    SELECT PERFIL_ID INTO usuarioIntegracao1PerfilId FROM PERFIL WHERE ENTITY_ID IN (SELECT ENTITY_ID FROM LOGIN WHERE LOGIN_NAME = usuarioIntegracao1) AND EREG_PORTAL_ID = gestorPortal;

    INSERT INTO PERFIL_PERMISSAO (PERFIL_ID, MODULO_ID, CREATION_DATE, PAPEL_ID, GESTOR_ID)  VALUES (usuarioIntegracao1PerfilId,'PRG0002',SYSDATE,35,gestorId); -- Operador do Pregão
    INSERT INTO PERFIL_PERMISSAO (PERFIL_ID, MODULO_ID, CREATION_DATE, PAPEL_ID, GESTOR_ID)  VALUES (usuarioIntegracao1PerfilId,'CDV0002',SYSDATE,36,gestorId); -- Operador Condicao de Venda
    INSERT INTO PERFIL_PERMISSAO (PERFIL_ID, MODULO_ID, CREATION_DATE, PAPEL_ID, GESTOR_ID)  VALUES (usuarioIntegracao1PerfilId,'LOT0002',SYSDATE,11,gestorId); -- Operador do modulo loteamento Superbid
    INSERT INTO PERFIL_PERMISSAO (PERFIL_ID, MODULO_ID, CREATION_DATE, PAPEL_ID, GESTOR_ID)  VALUES (usuarioIntegracao1PerfilId,'CCF',SYSDATE,71,gestorId); -- Adminstrador do Modulo
    INSERT INTO PERFIL_PERMISSAO (PERFIL_ID, MODULO_ID, CREATION_DATE, PAPEL_ID, GESTOR_ID)  VALUES (usuarioIntegracao1PerfilId,'CPC',SYSDATE,106,gestorId); -- Administrador do Módulo
    INSERT INTO PERFIL_PERMISSAO (PERFIL_ID, MODULO_ID, CREATION_DATE, PAPEL_ID, GESTOR_ID)  VALUES (usuarioIntegracao1PerfilId,'CDA',SYSDATE,111,gestorId); -- Adminstrador CDA - GATE 1.0

    -- Dar acesso as APIS ao usuario do administrativo ( GATE , Plataforma Leiloes, etc.. )
    SELECT PERFIL_ID INTO usuarioIntegracao2PerfilId FROM PERFIL WHERE ENTITY_ID IN (SELECT ENTITY_ID FROM LOGIN WHERE LOGIN_NAME = usuarioIntegracao2) AND EREG_PORTAL_ID = gestorPortal;

    INSERT INTO PERFIL_PERMISSAO (PERFIL_ID, MODULO_ID, CREATION_DATE, PAPEL_ID, GESTOR_ID)  VALUES (usuarioIntegracao2PerfilId,'PRG0002',SYSDATE,35,gestorId); -- Operador do Pregão
    INSERT INTO PERFIL_PERMISSAO (PERFIL_ID, MODULO_ID, CREATION_DATE, PAPEL_ID, GESTOR_ID)  VALUES (usuarioIntegracao2PerfilId,'CDV0002',SYSDATE,36,gestorId); -- Operador Condicao de Venda
    INSERT INTO PERFIL_PERMISSAO (PERFIL_ID, MODULO_ID, CREATION_DATE, PAPEL_ID, GESTOR_ID)  VALUES (usuarioIntegracao2PerfilId,'LOT0002',SYSDATE,11,gestorId); -- Operador do modulo loteamento Superbid
    INSERT INTO PERFIL_PERMISSAO (PERFIL_ID, MODULO_ID, CREATION_DATE, PAPEL_ID, GESTOR_ID)  VALUES (usuarioIntegracao2PerfilId,'CCF',SYSDATE,71,gestorId); -- Adminstrador do Modulo
    INSERT INTO PERFIL_PERMISSAO (PERFIL_ID, MODULO_ID, CREATION_DATE, PAPEL_ID, GESTOR_ID)  VALUES (usuarioIntegracao2PerfilId,'CPC',SYSDATE,106,gestorId); -- Administrador do Módulo
    INSERT INTO PERFIL_PERMISSAO (PERFIL_ID, MODULO_ID, CREATION_DATE, PAPEL_ID, GESTOR_ID)  VALUES (usuarioIntegracao2PerfilId,'CDA',SYSDATE,111,gestorId); -- Adminstrador CDA - GATE 1.0

    -- SETUP TRANSACIONAL FINANCEIRO

    -- Forma de Pagamento
    INSERT INTO FL_FORMA_PAGAMENTO_GESTOR VALUES(gestorId,2); --Depósito
    INSERT INTO FL_FORMA_PAGAMENTO_GESTOR VALUES(gestorId,9); --S4Payments
    INSERT INTO FL_FORMA_PAGAMENTO_GESTOR VALUES(gestorId,11); --Guia de depósito Judicial

    -- Itens de Pagamento - 1º Split
    INSERT INTO FL_TIPO_ITEM_PAG_GESTOR(COD_GESTOR, COD_TIPO_ITEM_PAGAMENTO, DATA_CRIACAO, STATUS, ORDEM_BAIXA) VALUES(gestorId, 1, SYSDATE, 'T', 3); --Pagamento do lote
    INSERT INTO FL_TIPO_ITEM_PAG_GESTOR(COD_GESTOR, COD_TIPO_ITEM_PAGAMENTO, DATA_CRIACAO, STATUS, ORDEM_BAIXA) VALUES(gestorId, 2, SYSDATE, 'T', 1); --Comissão do leiloeiro
    INSERT INTO FL_TIPO_ITEM_PAG_GESTOR(COD_GESTOR, COD_TIPO_ITEM_PAGAMENTO, DATA_CRIACAO, STATUS, ORDEM_BAIXA) VALUES(gestorId, 5, SYSDATE, 'T', 2); --Encargos de Administração
    INSERT INTO FL_TIPO_ITEM_PAG_GESTOR(COD_GESTOR, COD_TIPO_ITEM_PAGAMENTO, DATA_CRIACAO, STATUS, ORDEM_BAIXA) VALUES(gestorId, 3, SYSDATE, 'T', 2); --Buyers

    -- Itens de Serviço - 2º Split
    INSERT INTO FL_TIPO_ITEM_SERV_GESTOR(COD_GESTOR, COD_TIPO_ITEM_SERVICO, STATUS) VALUES(gestorId, 1, 'T'); --Vendedor
    INSERT INTO FL_TIPO_ITEM_SERV_GESTOR(COD_GESTOR, COD_TIPO_ITEM_SERVICO, STATUS) VALUES(gestorId, 3, 'T'); --Assessoria

    -- SETUP LOJA
    INSERT INTO SBINS.STORE (ID, NAME,CREATED_AT,UPDATED_AT,PORTAL_ID,VISIBLE_ON_PORTAL,HIGHLIGHT,LOGO_URI,DESCRIPTION,POSITION,EXTERNAL_LINK,VISIBLE_ON_PORTAL_BANNER,LAST_UPDATE_DATE,STORE_URI) 
    values ((SELECT MAX(ID)+1 FROM STORE),UPPER(storeNome),SYSDATE,SYSDATE,15,'T','T',gestorLogo,UPPER(storeNome),null,null,'T',SYSDATE,storeUri) RETURNING ID INTO storeId;

    INSERT INTO REL_STORE_EVENT_MANAGER ( STORE_ID, EVENT_MANAGER_ID ) VALUES ( storeId, gestorId );

    -- SETUP LEILOEIRO
    IF numeroRegistroJunta IS NOT NULL THEN
        SELECT COUNT(*) INTO v_exists FROM INTER_ENTITY WHERE ENTITY_ID = gestorEntityId AND ENTITY_PARENT_ID = gestorEntityId AND ROLE_ID = 11;
        IF v_exists = 0 THEN
        INSERT INTO INTER_ENTITY (ENTITY_ID, ENTITY_PARENT_ID, ROLE_ID)
        VALUES (gestorEntityId, gestorEntityId, 11);
        END IF;

        SELECT COUNT(*) INTO v_exists FROM DOCUMENT WHERE DOCUMENT_NUMBER = numeroRegistroJunta AND DOCUMENT_TYPE_ID = 6 AND ENTITY_ID = gestorEntityId;
        IF v_exists = 0 THEN
        INSERT INTO DOCUMENT (DOCUMENT_NUMBER, DOCUMENT_TYPE_ID, ENTITY_ID)
        VALUES (numeroRegistroJunta, 6, gestorEntityId);
        END IF;

        SELECT COUNT(*) INTO v_exists FROM REL_GESTOR_AUCTIONEER WHERE GESTOR_ID = gestorId AND ENTITY_ID = gestorEntityId;
        IF v_exists = 0 THEN
        INSERT INTO REL_GESTOR_AUCTIONEER (GESTOR_ID, ENTITY_ID)
        VALUES (gestorId, gestorEntityId);
        END IF;
    END IF;

    -- NOVO PERMISSIONAMENTO FINLEI
    INSERT INTO gestor_acesso (GESTOR_ID,GESTOR_ID_PAI) VALUES(gestorId,114);

    -- CRIAR CONDICAO DE PLATAFORMA
    --insert into fl_ccvenda (COD_CONDICAO_COMERCIAL,DESC_CONDICAO_COMERCIAL,COD_TIPO_TRANSACAO,COD_GESTOR,COD_VENDEDOR,COD_EVENTO,COD_OFERTA,COD_FORMA_PAGAMENTO,COD_FAVORECIDO,DIAS_VENCIMENTO,INSTRUCAO_PAGAMENTO,DATA_CRIACAO,DATA_ATUALIZACAO,COD_STATUS,MIN_PORCENTAGEM_ENTRADA,MAX_QUANTIDADE_PARCELAS,AFTER_CASHOUT,COBRANCA_PLATAFORMA,DATA_EXPIRACAO,DIAS_CONDICIONAL,TIPO_FAVORECIDO)
    -- values ((SELECT MAX(COD_CONDICAO_COMERCIAL)+1 FROM fl_ccvenda),gestorId || ' ' || gestorNome || ' - TABELA ' || gestorTabela,1,gestorId,null,null,null,null,null,null,null,SYSDATE,SYSDATE,2,null,null,null,'T',null,null,null) RETURNING COD_CONDICAO_COMERCIAL INTO codCondicaoComercial;
    --insert into fl_ccvenda_item (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_FORMA_PAGAMENTO,COD_FAVORECIDO,COD_CONTA_PAG_FAVORECIDO,COD_TIPO_COBRANCA,PORCENTAGEM,VALOR,VALOR_MAXIMO)
    --  values (codCondicaoComercial,2,9,gestorEntityId,null,2,5,null,null);
    --insert into fl_ccvenda_split (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_TIPO_ITEM_SERVICO,COD_FAVORECIDO,COD_TIPO_COBRANCA,COD_BASE_CALCULO,PORCENTAGEM,VALOR,VALOR_MAXIMO)
    --  values (codCondicaoComercial,2,2,1399790,3,1,null,null,null);

    /*  INICIO TABELA 1
    IF gestorTabela = 1 THEN

        insert into fl_ccvenda_split_faixa (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_TIPO_ITEM_SERVICO,VALOR_INICIAL,VALOR_FINAL,PORCENTAGEM,VALOR)
            values (codCondicaoComercial,'2','2','3000,01','10000',null,'50');
        insert into fl_ccvenda_split_faixa (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_TIPO_ITEM_SERVICO,VALOR_INICIAL,VALOR_FINAL,PORCENTAGEM,VALOR)
            values (codCondicaoComercial,'2','2','10000,01','30000',null,'150');
        insert into fl_ccvenda_split_faixa (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_TIPO_ITEM_SERVICO,VALOR_INICIAL,VALOR_FINAL,PORCENTAGEM,VALOR)
            values (codCondicaoComercial,'2','2','30000,01','100000',null,'250');
        insert into fl_ccvenda_split_faixa (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_TIPO_ITEM_SERVICO,VALOR_INICIAL,VALOR_FINAL,PORCENTAGEM,VALOR)
            values (codCondicaoComercial,'2','2','100000,01','999999999999',null,'350');

    END IF; 

    -- FIM TABELA 1

    -- INICIO TABELA 2
    IF gestorTabela = 2 THEN

        insert into fl_ccvenda_split_faixa (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_TIPO_ITEM_SERVICO,VALOR_INICIAL,VALOR_FINAL,PORCENTAGEM,VALOR)
            values (codCondicaoComercial,'2','2','3000,01','10000',null,'50');
        insert into fl_ccvenda_split_faixa (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_TIPO_ITEM_SERVICO,VALOR_INICIAL,VALOR_FINAL,PORCENTAGEM,VALOR)
            values (codCondicaoComercial,'2','2','10000,01','30000',null,'150');
        insert into fl_ccvenda_split_faixa (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_TIPO_ITEM_SERVICO,VALOR_INICIAL,VALOR_FINAL,PORCENTAGEM,VALOR)
            values (codCondicaoComercial,'2','2','30000,01','100000',null,'350');
        insert into fl_ccvenda_split_faixa (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_TIPO_ITEM_SERVICO,VALOR_INICIAL,VALOR_FINAL,PORCENTAGEM,VALOR)
            values (codCondicaoComercial,'2','2','100000,01','300000',null,'600');
        insert into fl_ccvenda_split_faixa (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_TIPO_ITEM_SERVICO,VALOR_INICIAL,VALOR_FINAL,PORCENTAGEM,VALOR)
            values (codCondicaoComercial,'2','2','300000,01','999999999999',null,'1000');

    END IF;

    -- FIM TABELA 2

    -- INICIO TABELA 3
    IF gestorTabela = 3 THEN

        insert into fl_ccvenda_split_faixa (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_TIPO_ITEM_SERVICO,VALOR_INICIAL,VALOR_FINAL,PORCENTAGEM,VALOR)
            values (codCondicaoComercial,'2','2','0','10000',null,'50');
        insert into fl_ccvenda_split_faixa (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_TIPO_ITEM_SERVICO,VALOR_INICIAL,VALOR_FINAL,PORCENTAGEM,VALOR)
            values (codCondicaoComercial,'2','2','10000,01','30000',null,'150');
        insert into fl_ccvenda_split_faixa (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_TIPO_ITEM_SERVICO,VALOR_INICIAL,VALOR_FINAL,PORCENTAGEM,VALOR)
            values (codCondicaoComercial,'2','2','30000,01','100000',null,'350');
        insert into fl_ccvenda_split_faixa (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_TIPO_ITEM_SERVICO,VALOR_INICIAL,VALOR_FINAL,PORCENTAGEM,VALOR)
            values (codCondicaoComercial,'2','2','100000,01','300000',null,'600');
        insert into fl_ccvenda_split_faixa (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_TIPO_ITEM_SERVICO,VALOR_INICIAL,VALOR_FINAL,PORCENTAGEM,VALOR)
            values (codCondicaoComercial,'2','2','300000,01','999999999999',null,'1000');

    END IF;

    -- FIM TABELA 3 */

    END;
    /
""",
        "nws": """
DECLARE
    gestorPortal NUMBER;
    usuarioIntegracao1 VARCHAR2(4000);
    usuarioIntegracao1PerfilId NUMBER;
    usuarioIntegracao2 VARCHAR2(4000);
    usuarioIntegracao2PerfilId NUMBER;
    gestorId NUMBER;
    gestorEntityId NUMBER;
    gestorNome VARCHAR2(4000);
    numeroRegistroJunta VARCHAR2(4000);
    storeId NUMBER;
    storeNome VARCHAR2(4000);
    gestorLogo VARCHAR2(4000);
    storeUri VARCHAR2(4000);
    gestorContactEmail VARCHAR2(4000);
    gestorTabela NUMBER;
    codCondicaoComercial NUMBER;
    leiloeiroEntityId NUMBER;
    isencaoDeTaxa VARCHAR2(1);
    v_exists NUMBER;
BEGIN
    gestorPortal := 2;
    usuarioIntegracao1 := 'nws.integracao';
    usuarioIntegracao2 := 'nws.integracao2';
    
    -- INICIO DADOS CUSTOMIZAVEIS
    gestorEntityId := {gestorEntityId};
    gestorNome := '{gestorNome}';
    storeNome := '{storeNome}';
    numeroRegistroJunta := '{numeroRegistroJunta}';
    SELECT NVL(MAX(GESTOR_ID), 0) + 1 INTO gestorId FROM GESTOR;
    gestorLogo := '{gestorLogo}';
    storeUri := '{storeUri}';
    gestorContactEmail := '{gestorContactEmail}';
    gestorTabela := {gestorTabela};
    leiloeiroEntityId := '{leiloeiroEntityId}';
    -- FIM DADOS CUSTOMIZAVEIS

    -- ETAPA 1 - CRIAR GESTOR

    -- Atribuir papel de gestor para entity
    SELECT COUNT(*) INTO v_exists FROM REL_ROLE_ENTITY WHERE ENTITY_ID = gestorEntityId AND ROLE_ID = 40;
    IF v_exists = 0 THEN
        INSERT INTO REL_ROLE_ENTITY (ENTITY_ID, ROLE_ID)
        VALUES (gestorEntityId, 40);
    END IF;

    SELECT COUNT(*) INTO v_exists FROM INTER_ENTITY WHERE ENTITY_ID = gestorEntityId AND ENTITY_PARENT_ID = gestorEntityId AND ROLE_ID = 40;
    IF v_exists = 0 THEN
        INSERT INTO INTER_ENTITY (ENTITY_ID, ENTITY_PARENT_ID, ROLE_ID)
        VALUES (gestorEntityId, gestorEntityId, 40);
    END IF;


    -- Cadastrar gestor 
    INSERT INTO GESTOR (GESTOR_ID, GESTOR, ENTITY_ID, GESTOR_TITLE, GESTOR_DESC, GESTOR_INATIVO, EREG_PORTAL_ID)
    VALUES (gestorId, gestorNome, gestorEntityId, gestorNome, gestorNome, 'F', gestorPortal);
    --desc gestor;
        
    INSERT INTO GESTOR_SETTINGS (GESTOR_ID,SHOW_ITENS_PORCENTAGEM,COUNTRY_CODE,COD_ERP_SYSTEM,ERP_KEY,AUTO_SALE_START,SYSTEM_CONTACT_EMAIL,AUTO_SALE_GENERATE,GESTOR_CONTACT_EMAIL,COD_PROJETO_LEILAO, PLATFORM_LICENSOR_ID) 
    values (gestorId,'2,3','1',2,'CORPORE_RM','01/01/1900','transaction-team@superbid.net','T',gestorContactEmail,130487, 2);



    INSERT INTO GESTOR_GEO_APPROVAL_DEFAULT (EREF_COUNTRY_CODE, GESTOR_ID) VALUES (1,gestorId);

    -- Projeto Comercial (61922 - Superbid Webservices)
    INSERT INTO COMMERCIAL_PROJECT (COMMERCIAL_PROJECT_DESC,COMMERCIAL_PROJECT_STATUS_ID,OWNER_ID,YOUR_REFERENCE,CREATED_AT,UPDATED_AT,CLOSE_AT,GESTOR_ID,ECONOMIC_GROUP_ID)
        values ('PROJETO PADRAO','1','61922','',SYSDATE,null,SYSDATE,gestorId,null);

    -- Dar acesso as APIS ao usuario do administrativo ( GATE , Plataforma Leiloes, etc.. )
    SELECT PERFIL_ID INTO usuarioIntegracao1PerfilId FROM PERFIL WHERE ENTITY_ID IN (SELECT ENTITY_ID FROM LOGIN WHERE LOGIN_NAME = usuarioIntegracao1) AND EREG_PORTAL_ID = gestorPortal;

    INSERT INTO PERFIL_PERMISSAO (PERFIL_ID, MODULO_ID, CREATION_DATE, PAPEL_ID, GESTOR_ID)  VALUES (usuarioIntegracao1PerfilId,'PRG0002',SYSDATE,35,gestorId); -- Operador do Pregão
    INSERT INTO PERFIL_PERMISSAO (PERFIL_ID, MODULO_ID, CREATION_DATE, PAPEL_ID, GESTOR_ID)  VALUES (usuarioIntegracao1PerfilId,'CDV0002',SYSDATE,36,gestorId); -- Operador Condicao de Venda
    INSERT INTO PERFIL_PERMISSAO (PERFIL_ID, MODULO_ID, CREATION_DATE, PAPEL_ID, GESTOR_ID)  VALUES (usuarioIntegracao1PerfilId,'LOT0002',SYSDATE,11,gestorId); -- Operador do modulo loteamento Superbid
    INSERT INTO PERFIL_PERMISSAO (PERFIL_ID, MODULO_ID, CREATION_DATE, PAPEL_ID, GESTOR_ID)  VALUES (usuarioIntegracao1PerfilId,'CCF',SYSDATE,71,gestorId); -- Adminstrador do Modulo
    INSERT INTO PERFIL_PERMISSAO (PERFIL_ID, MODULO_ID, CREATION_DATE, PAPEL_ID, GESTOR_ID)  VALUES (usuarioIntegracao1PerfilId,'CPC',SYSDATE,106,gestorId); -- Administrador do Módulo
    INSERT INTO PERFIL_PERMISSAO (PERFIL_ID, MODULO_ID, CREATION_DATE, PAPEL_ID, GESTOR_ID)  VALUES (usuarioIntegracao1PerfilId,'CDA',SYSDATE,111,gestorId); -- Adminstrador CDA - GATE 1.0

    -- Dar acesso as APIS ao usuario do administrativo ( GATE , Plataforma Leiloes, etc.. )
    SELECT PERFIL_ID INTO usuarioIntegracao2PerfilId FROM PERFIL WHERE ENTITY_ID IN (SELECT ENTITY_ID FROM LOGIN WHERE LOGIN_NAME = usuarioIntegracao2) AND EREG_PORTAL_ID = gestorPortal;

    INSERT INTO PERFIL_PERMISSAO (PERFIL_ID, MODULO_ID, CREATION_DATE, PAPEL_ID, GESTOR_ID)  VALUES (usuarioIntegracao2PerfilId,'PRG0002',SYSDATE,35,gestorId); -- Operador do Pregão
    INSERT INTO PERFIL_PERMISSAO (PERFIL_ID, MODULO_ID, CREATION_DATE, PAPEL_ID, GESTOR_ID)  VALUES (usuarioIntegracao2PerfilId,'CDV0002',SYSDATE,36,gestorId); -- Operador Condicao de Venda
    INSERT INTO PERFIL_PERMISSAO (PERFIL_ID, MODULO_ID, CREATION_DATE, PAPEL_ID, GESTOR_ID)  VALUES (usuarioIntegracao2PerfilId,'LOT0002',SYSDATE,11,gestorId); -- Operador do modulo loteamento Superbid
    INSERT INTO PERFIL_PERMISSAO (PERFIL_ID, MODULO_ID, CREATION_DATE, PAPEL_ID, GESTOR_ID)  VALUES (usuarioIntegracao2PerfilId,'CCF',SYSDATE,71,gestorId); -- Adminstrador do Modulo
    INSERT INTO PERFIL_PERMISSAO (PERFIL_ID, MODULO_ID, CREATION_DATE, PAPEL_ID, GESTOR_ID)  VALUES (usuarioIntegracao2PerfilId,'CPC',SYSDATE,106,gestorId); -- Administrador do Módulo
    INSERT INTO PERFIL_PERMISSAO (PERFIL_ID, MODULO_ID, CREATION_DATE, PAPEL_ID, GESTOR_ID)  VALUES (usuarioIntegracao2PerfilId,'CDA',SYSDATE,111,gestorId); -- Adminstrador CDA - GATE 1.0

    -- SETUP TRANSACIONAL FINANCEIRO

    -- Forma de Pagamento
    INSERT INTO FL_FORMA_PAGAMENTO_GESTOR VALUES(gestorId,2); --Depósito
    INSERT INTO FL_FORMA_PAGAMENTO_GESTOR VALUES(gestorId,9); --S4Payments
    INSERT INTO FL_FORMA_PAGAMENTO_GESTOR VALUES(gestorId,11); --Guia de depósito Judicial

    -- Itens de Pagamento - 1º Split
    INSERT INTO FL_TIPO_ITEM_PAG_GESTOR(COD_GESTOR, COD_TIPO_ITEM_PAGAMENTO, DATA_CRIACAO, STATUS, ORDEM_BAIXA) VALUES(gestorId, 1, SYSDATE, 'T', 3); --Pagamento do lote
    INSERT INTO FL_TIPO_ITEM_PAG_GESTOR(COD_GESTOR, COD_TIPO_ITEM_PAGAMENTO, DATA_CRIACAO, STATUS, ORDEM_BAIXA) VALUES(gestorId, 2, SYSDATE, 'T', 1); --Comissão do leiloeiro
    INSERT INTO FL_TIPO_ITEM_PAG_GESTOR(COD_GESTOR, COD_TIPO_ITEM_PAGAMENTO, DATA_CRIACAO, STATUS, ORDEM_BAIXA) VALUES(gestorId, 5, SYSDATE, 'T', 2); --Encargos de Administração
    INSERT INTO FL_TIPO_ITEM_PAG_GESTOR(COD_GESTOR, COD_TIPO_ITEM_PAGAMENTO, DATA_CRIACAO, STATUS, ORDEM_BAIXA) VALUES(gestorId, 3, SYSDATE, 'T', 2); --Buyers

    -- Itens de Serviço - 2º Split
    INSERT INTO FL_TIPO_ITEM_SERV_GESTOR(COD_GESTOR, COD_TIPO_ITEM_SERVICO, STATUS) VALUES(gestorId, 1, 'T'); --Vendedor
    INSERT INTO FL_TIPO_ITEM_SERV_GESTOR(COD_GESTOR, COD_TIPO_ITEM_SERVICO, STATUS) VALUES(gestorId, 2, 'T'); --Licenciamento
    INSERT INTO FL_TIPO_ITEM_SERV_GESTOR(COD_GESTOR, COD_TIPO_ITEM_SERVICO, STATUS) VALUES(gestorId, 3, 'T'); --Assessoria

    -- SETUP LOJA
    INSERT INTO SBINS.STORE (ID, NAME,CREATED_AT,UPDATED_AT,PORTAL_ID,VISIBLE_ON_PORTAL,HIGHLIGHT,LOGO_URI,DESCRIPTION,POSITION,EXTERNAL_LINK,VISIBLE_ON_PORTAL_BANNER,LAST_UPDATE_DATE,STORE_URI) 
    values ((SELECT MAX(ID)+1 FROM STORE),UPPER(storeNome),SYSDATE,SYSDATE,2,'T','T',gestorLogo,UPPER(storeNome),null,null,'T',SYSDATE,storeUri) RETURNING ID INTO storeId;

    INSERT INTO REL_STORE_EVENT_MANAGER ( STORE_ID, EVENT_MANAGER_ID ) VALUES ( storeId, gestorId );

    -- SETUP LEILOEIRO
    IF numeroRegistroJunta IS NOT NULL THEN
        SELECT COUNT(*) INTO v_exists FROM INTER_ENTITY WHERE ENTITY_ID = gestorEntityId AND ENTITY_PARENT_ID = gestorEntityId AND ROLE_ID = 11;
        IF v_exists = 0 THEN
        INSERT INTO INTER_ENTITY (ENTITY_ID, ENTITY_PARENT_ID, ROLE_ID)
        VALUES (gestorEntityId, gestorEntityId, 11);
        END IF;

        SELECT COUNT(*) INTO v_exists FROM DOCUMENT WHERE DOCUMENT_NUMBER = numeroRegistroJunta AND DOCUMENT_TYPE_ID = 6 AND ENTITY_ID = gestorEntityId;
        IF v_exists = 0 THEN
        INSERT INTO DOCUMENT (DOCUMENT_NUMBER, DOCUMENT_TYPE_ID, ENTITY_ID)
        VALUES (numeroRegistroJunta, 6, gestorEntityId);
        END IF;

        SELECT COUNT(*) INTO v_exists FROM REL_GESTOR_AUCTIONEER WHERE GESTOR_ID = gestorId AND ENTITY_ID = gestorEntityId;
        IF v_exists = 0 THEN
        INSERT INTO REL_GESTOR_AUCTIONEER (GESTOR_ID, ENTITY_ID)
        VALUES (gestorId, gestorEntityId);
        END IF;
    END IF;

    -- NOVO PERMISSIONAMENTO FINLEI
    INSERT INTO gestor_acesso (GESTOR_ID,GESTOR_ID_PAI) VALUES(gestorId,114);

    -- CRIAR CONDICAO DE PLATAFORMA
    insert into fl_ccvenda (COD_CONDICAO_COMERCIAL,DESC_CONDICAO_COMERCIAL,COD_TIPO_TRANSACAO,COD_GESTOR,COD_VENDEDOR,COD_EVENTO,COD_OFERTA,COD_FORMA_PAGAMENTO,COD_FAVORECIDO,DIAS_VENCIMENTO,INSTRUCAO_PAGAMENTO,DATA_CRIACAO,DATA_ATUALIZACAO,COD_STATUS,MIN_PORCENTAGEM_ENTRADA,MAX_QUANTIDADE_PARCELAS,AFTER_CASHOUT,COBRANCA_PLATAFORMA,DATA_EXPIRACAO,DIAS_CONDICIONAL,TIPO_FAVORECIDO)
    values ((SELECT MAX(COD_CONDICAO_COMERCIAL)+1 FROM fl_ccvenda),gestorId || ' ' || gestorNome || ' - TABELA ' || gestorTabela,1,gestorId,null,null,null,null,null,null,null,SYSDATE,SYSDATE,2,null,null,null,'T',null,null,null) RETURNING COD_CONDICAO_COMERCIAL INTO codCondicaoComercial;


    insert into fl_ccvenda_item (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO) values (codCondicaoComercial,2);


    insert into fl_ccvenda_split (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_TIPO_ITEM_SERVICO,COD_FAVORECIDO,COD_TIPO_COBRANCA,COD_BASE_CALCULO,PORCENTAGEM,VALOR,VALOR_MAXIMO)
    values (codCondicaoComercial,2,2,1399790,3,1,null,null,null);

    -- INICIO TABELA 1
    IF gestorTabela = 1 THEN

        insert into fl_ccvenda_split_faixa (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_TIPO_ITEM_SERVICO,VALOR_INICIAL,VALOR_FINAL,PORCENTAGEM,VALOR)
            values (codCondicaoComercial,'2','2','3000,01','10000',null,'50');
        insert into fl_ccvenda_split_faixa (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_TIPO_ITEM_SERVICO,VALOR_INICIAL,VALOR_FINAL,PORCENTAGEM,VALOR)
            values (codCondicaoComercial,'2','2','10000,01','30000',null,'150');
        insert into fl_ccvenda_split_faixa (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_TIPO_ITEM_SERVICO,VALOR_INICIAL,VALOR_FINAL,PORCENTAGEM,VALOR)
            values (codCondicaoComercial,'2','2','30000,01','100000',null,'250');
        insert into fl_ccvenda_split_faixa (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_TIPO_ITEM_SERVICO,VALOR_INICIAL,VALOR_FINAL,PORCENTAGEM,VALOR)
            values (codCondicaoComercial,'2','2','100000,01','999999999999',null,'350');

    END IF;

    -- FIM TABELA 1

    -- INICIO TABELA 2
    IF gestorTabela = 2 THEN

        insert into fl_ccvenda_split_faixa (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_TIPO_ITEM_SERVICO,VALOR_INICIAL,VALOR_FINAL,PORCENTAGEM,VALOR)
            values (codCondicaoComercial,'2','2','3000,01','10000',null,'50');
        insert into fl_ccvenda_split_faixa (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_TIPO_ITEM_SERVICO,VALOR_INICIAL,VALOR_FINAL,PORCENTAGEM,VALOR)
            values (codCondicaoComercial,'2','2','10000,01','30000',null,'150');
        insert into fl_ccvenda_split_faixa (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_TIPO_ITEM_SERVICO,VALOR_INICIAL,VALOR_FINAL,PORCENTAGEM,VALOR)
            values (codCondicaoComercial,'2','2','30000,01','100000',null,'350');
        insert into fl_ccvenda_split_faixa (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_TIPO_ITEM_SERVICO,VALOR_INICIAL,VALOR_FINAL,PORCENTAGEM,VALOR)
            values (codCondicaoComercial,'2','2','100000,01','300000',null,'600');
        insert into fl_ccvenda_split_faixa (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_TIPO_ITEM_SERVICO,VALOR_INICIAL,VALOR_FINAL,PORCENTAGEM,VALOR)
            values (codCondicaoComercial,'2','2','300000,01','999999999999',null,'1000');

    END IF;

    -- FIM TABELA 2

    -- INICIO TABELA 3
    IF gestorTabela = 3 THEN

        insert into fl_ccvenda_split_faixa (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_TIPO_ITEM_SERVICO,VALOR_INICIAL,VALOR_FINAL,PORCENTAGEM,VALOR)
            values (codCondicaoComercial,'2','2','0','10000',null,'50');
        insert into fl_ccvenda_split_faixa (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_TIPO_ITEM_SERVICO,VALOR_INICIAL,VALOR_FINAL,PORCENTAGEM,VALOR)
            values (codCondicaoComercial,'2','2','10000,01','30000',null,'150');
        insert into fl_ccvenda_split_faixa (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_TIPO_ITEM_SERVICO,VALOR_INICIAL,VALOR_FINAL,PORCENTAGEM,VALOR)
            values (codCondicaoComercial,'2','2','30000,01','100000',null,'350');
        insert into fl_ccvenda_split_faixa (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_TIPO_ITEM_SERVICO,VALOR_INICIAL,VALOR_FINAL,PORCENTAGEM,VALOR)
            values (codCondicaoComercial,'2','2','100000,01','300000',null,'600');
        insert into fl_ccvenda_split_faixa (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_TIPO_ITEM_SERVICO,VALOR_INICIAL,VALOR_FINAL,PORCENTAGEM,VALOR)
            values (codCondicaoComercial,'2','2','300000,01','999999999999',null,'1000');

    END IF;

    -- FIM TABELA 3

    -- INICIO TABELA 4
    IF gestorTabela = 4 THEN

        insert into fl_ccvenda_split_faixa (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_TIPO_ITEM_SERVICO,VALOR_INICIAL,VALOR_FINAL,PORCENTAGEM,VALOR)
            values (codCondicaoComercial,'2','2','1','1000',null,'10');
        insert into fl_ccvenda_split_faixa (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_TIPO_ITEM_SERVICO,VALOR_INICIAL,VALOR_FINAL,PORCENTAGEM,VALOR)
            values (codCondicaoComercial,'2','2','1000,01','2000',null,'25');
        insert into fl_ccvenda_split_faixa (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_TIPO_ITEM_SERVICO,VALOR_INICIAL,VALOR_FINAL,PORCENTAGEM,VALOR)
            values (codCondicaoComercial,'2','2','2000,01','5000',null,'50');
        insert into fl_ccvenda_split_faixa (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_TIPO_ITEM_SERVICO,VALOR_INICIAL,VALOR_FINAL,PORCENTAGEM,VALOR)
            values (codCondicaoComercial,'2','2','5000,01','10000',null,'120');
        insert into fl_ccvenda_split_faixa (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_TIPO_ITEM_SERVICO,VALOR_INICIAL,VALOR_FINAL,PORCENTAGEM,VALOR)
            values (codCondicaoComercial,'2','2','10000,01','30000',null,'250');
        insert into fl_ccvenda_split_faixa (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_TIPO_ITEM_SERVICO,VALOR_INICIAL,VALOR_FINAL,PORCENTAGEM,VALOR)
            values (codCondicaoComercial,'2','2','30000,01','70000',null,'500');
        insert into fl_ccvenda_split_faixa (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_TIPO_ITEM_SERVICO,VALOR_INICIAL,VALOR_FINAL,PORCENTAGEM,VALOR)
            values (codCondicaoComercial,'2','2','70000,01','150000',null,'1000');
        insert into fl_ccvenda_split_faixa (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_TIPO_ITEM_SERVICO,VALOR_INICIAL,VALOR_FINAL,PORCENTAGEM,VALOR)
            values (codCondicaoComercial,'2','2','150000,01','300000',null,'2000');
        insert into fl_ccvenda_split_faixa (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_TIPO_ITEM_SERVICO,VALOR_INICIAL,VALOR_FINAL,PORCENTAGEM,VALOR)
            values (codCondicaoComercial,'2','2','300000,01','500000',null,'3000');
        insert into fl_ccvenda_split_faixa (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_TIPO_ITEM_SERVICO,VALOR_INICIAL,VALOR_FINAL,PORCENTAGEM,VALOR)
            values (codCondicaoComercial,'2','2','500000,01','1000000',null,'5000');
        insert into fl_ccvenda_split_faixa (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_TIPO_ITEM_SERVICO,VALOR_INICIAL,VALOR_FINAL,PORCENTAGEM,VALOR)
            values (codCondicaoComercial,'2','2','1000000,01','1500000',null,'8000');
        insert into fl_ccvenda_split_faixa (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_TIPO_ITEM_SERVICO,VALOR_INICIAL,VALOR_FINAL,PORCENTAGEM,VALOR)
            values (codCondicaoComercial,'2','2','1500000,01','3000000',null,'10000');
        insert into fl_ccvenda_split_faixa (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_TIPO_ITEM_SERVICO,VALOR_INICIAL,VALOR_FINAL,PORCENTAGEM,VALOR)
            values (codCondicaoComercial,'2','2','3000000,01','5000000',null,'20000');
        insert into fl_ccvenda_split_faixa (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_TIPO_ITEM_SERVICO,VALOR_INICIAL,VALOR_FINAL,PORCENTAGEM,VALOR)
            values (codCondicaoComercial,'2','2','5000000,01','10000000',null,'30000');
        insert into fl_ccvenda_split_faixa (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_TIPO_ITEM_SERVICO,VALOR_INICIAL,VALOR_FINAL,PORCENTAGEM,VALOR)
            values (codCondicaoComercial,'2','2','10000000,01','50000000',null,'40000');
        insert into fl_ccvenda_split_faixa (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_TIPO_ITEM_SERVICO,VALOR_INICIAL,VALOR_FINAL,PORCENTAGEM,VALOR)
            values (codCondicaoComercial,'2','2','50000000,01','999999999999',null,'75000');

    END IF;

    -- FIM TABELA 4

    --INICIO TABELA 5

    IF gestorTabela = 5 THEN

        insert into fl_ccvenda_split_faixa (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_TIPO_ITEM_SERVICO,VALOR_INICIAL,VALOR_FINAL,PORCENTAGEM,VALOR)
            values (codCondicaoComercial,'2','2','1','1000',null,'10');
        insert into fl_ccvenda_split_faixa (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_TIPO_ITEM_SERVICO,VALOR_INICIAL,VALOR_FINAL,PORCENTAGEM,VALOR)
            values (codCondicaoComercial,'2','2','1000,01','2000',null,'25');
        insert into fl_ccvenda_split_faixa (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_TIPO_ITEM_SERVICO,VALOR_INICIAL,VALOR_FINAL,PORCENTAGEM,VALOR)
            values (codCondicaoComercial,'2','2','2000,01','5000',null,'50');
        insert into fl_ccvenda_split_faixa (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_TIPO_ITEM_SERVICO,VALOR_INICIAL,VALOR_FINAL,PORCENTAGEM,VALOR)
            values (codCondicaoComercial,'2','2','5000,01','10000',null,'120');
        insert into fl_ccvenda_split_faixa (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_TIPO_ITEM_SERVICO,VALOR_INICIAL,VALOR_FINAL,PORCENTAGEM,VALOR)
            values (codCondicaoComercial,'2','2','10000,01','30000',null,'250');
        insert into fl_ccvenda_split_faixa (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_TIPO_ITEM_SERVICO,VALOR_INICIAL,VALOR_FINAL,PORCENTAGEM,VALOR)
            values (codCondicaoComercial,'2','2','30000,01','70000',null,'500');
        insert into fl_ccvenda_split_faixa (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_TIPO_ITEM_SERVICO,VALOR_INICIAL,VALOR_FINAL,PORCENTAGEM,VALOR)
            values (codCondicaoComercial,'2','2','70000,01','150000',null,'1000');
        insert into fl_ccvenda_split_faixa (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_TIPO_ITEM_SERVICO,VALOR_INICIAL,VALOR_FINAL,PORCENTAGEM,VALOR)
            values (codCondicaoComercial,'2','2','150000,01','300000',null,'2000');
        insert into fl_ccvenda_split_faixa (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_TIPO_ITEM_SERVICO,VALOR_INICIAL,VALOR_FINAL,PORCENTAGEM,VALOR)
            values (codCondicaoComercial,'2','2','300000,01','500000',null,'3000');
        insert into fl_ccvenda_split_faixa (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_TIPO_ITEM_SERVICO,VALOR_INICIAL,VALOR_FINAL,PORCENTAGEM,VALOR)
            values (codCondicaoComercial,'2','2','500000,01','1000000',null,'5000');
        insert into fl_ccvenda_split_faixa (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_TIPO_ITEM_SERVICO,VALOR_INICIAL,VALOR_FINAL,PORCENTAGEM,VALOR)
            values (codCondicaoComercial,'2','2','1000000,01','1500000',null,'8000');
        insert into fl_ccvenda_split_faixa (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_TIPO_ITEM_SERVICO,VALOR_INICIAL,VALOR_FINAL,PORCENTAGEM,VALOR)
            values (codCondicaoComercial,'2','2','1500000,01','3000000',null,'10000');
        insert into fl_ccvenda_split_faixa (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_TIPO_ITEM_SERVICO,VALOR_INICIAL,VALOR_FINAL,PORCENTAGEM,VALOR)
            values (codCondicaoComercial,'2','2','3000000,01','5000000',null,'20000');
        insert into fl_ccvenda_split_faixa (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_TIPO_ITEM_SERVICO,VALOR_INICIAL,VALOR_FINAL,PORCENTAGEM,VALOR)
            values (codCondicaoComercial,'2','2','5000000,01','10000000',null,'30000');
        insert into fl_ccvenda_split_faixa (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_TIPO_ITEM_SERVICO,VALOR_INICIAL,VALOR_FINAL,PORCENTAGEM,VALOR)
            values (codCondicaoComercial,'2','2','10000000,01','50000000',null,'40000');

    END IF;

    --FIM TABELA 5

    --Fim da tabela 5

    IF gestorTabela = 6 THEN

        insert into fl_ccvenda_split_faixa (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_TIPO_ITEM_SERVICO,VALOR_INICIAL,VALOR_FINAL,PORCENTAGEM,VALOR)
            values (codCondicaoComercial,'2','2','1','1000',null,'10');
        insert into fl_ccvenda_split_faixa (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_TIPO_ITEM_SERVICO,VALOR_INICIAL,VALOR_FINAL,PORCENTAGEM,VALOR)
            values (codCondicaoComercial,'2','2','1000,01','2000',null,'25');
        insert into fl_ccvenda_split_faixa (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_TIPO_ITEM_SERVICO,VALOR_INICIAL,VALOR_FINAL,PORCENTAGEM,VALOR)
            values (codCondicaoComercial,'2','2','2000,01','5000',null,'50');
        insert into fl_ccvenda_split_faixa (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_TIPO_ITEM_SERVICO,VALOR_INICIAL,VALOR_FINAL,PORCENTAGEM,VALOR)
            values (codCondicaoComercial,'2','2','5000,01','10000',null,'120');
        insert into fl_ccvenda_split_faixa (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_TIPO_ITEM_SERVICO,VALOR_INICIAL,VALOR_FINAL,PORCENTAGEM,VALOR)
            values (codCondicaoComercial,'2','2','10000,01','30000',null,'250');
        insert into fl_ccvenda_split_faixa (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_TIPO_ITEM_SERVICO,VALOR_INICIAL,VALOR_FINAL,PORCENTAGEM,VALOR)
            values (codCondicaoComercial,'2','2','30000,01','70000',null,'500');
        insert into fl_ccvenda_split_faixa (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_TIPO_ITEM_SERVICO,VALOR_INICIAL,VALOR_FINAL,PORCENTAGEM,VALOR)
            values (codCondicaoComercial,'2','2','70000,01','150000',null,'1000');
        insert into fl_ccvenda_split_faixa (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_TIPO_ITEM_SERVICO,VALOR_INICIAL,VALOR_FINAL,PORCENTAGEM,VALOR)
            values (codCondicaoComercial,'2','2','150000,01','300000',null,'2000');
        insert into fl_ccvenda_split_faixa (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_TIPO_ITEM_SERVICO,VALOR_INICIAL,VALOR_FINAL,PORCENTAGEM,VALOR)
            values (codCondicaoComercial,'2','2','300000,01','500000',null,'3000');
        insert into fl_ccvenda_split_faixa (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_TIPO_ITEM_SERVICO,VALOR_INICIAL,VALOR_FINAL,PORCENTAGEM,VALOR)
            values (codCondicaoComercial,'2','2','500000,01','1000000',null,'5000');
        insert into fl_ccvenda_split_faixa (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_TIPO_ITEM_SERVICO,VALOR_INICIAL,VALOR_FINAL,PORCENTAGEM,VALOR)
            values (codCondicaoComercial,'2','2','1000000,01','1500000',null,'8000');
        insert into fl_ccvenda_split_faixa (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_TIPO_ITEM_SERVICO,VALOR_INICIAL,VALOR_FINAL,PORCENTAGEM,VALOR)
            values (codCondicaoComercial,'2','2','1500000,01','3000000',null,'10000');
        insert into fl_ccvenda_split_faixa (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_TIPO_ITEM_SERVICO,VALOR_INICIAL,VALOR_FINAL,PORCENTAGEM,VALOR)
            values (codCondicaoComercial,'2','2','3000000,01','5000000',null,'20000');
        insert into fl_ccvenda_split_faixa (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_TIPO_ITEM_SERVICO,VALOR_INICIAL,VALOR_FINAL,PORCENTAGEM,VALOR)
            values (codCondicaoComercial,'2','2','5000000,01','10000000',null,'30000');
        insert into fl_ccvenda_split_faixa (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_TIPO_ITEM_SERVICO,VALOR_INICIAL,VALOR_FINAL,PORCENTAGEM,VALOR)
            values (codCondicaoComercial,'2','2','10000000,01','50000000',null,'40000');
        insert into fl_ccvenda_split_faixa (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_TIPO_ITEM_SERVICO,VALOR_INICIAL,VALOR_FINAL,PORCENTAGEM,VALOR)
            values (codCondicaoComercial,'2','2','50000000,01','999999999999,999',null,'75000');

    END IF;


    END;
    /
""",
        "sold": """
DECLARE
    gestorPortal NUMBER;
    usuarioIntegracao1 VARCHAR2(4000);
    usuarioIntegracao1PerfilId NUMBER;
    usuarioIntegracao2 VARCHAR2(4000);
    usuarioIntegracao2PerfilId NUMBER;
    gestorId NUMBER;
    gestorEntityId NUMBER;
    gestorNome VARCHAR2(4000);
    numeroRegistroJunta VARCHAR2(4000);
    storeId NUMBER;
    storeNome VARCHAR2(4000);
    gestorLogo VARCHAR2(4000);
    storeUri VARCHAR2(4000);
    gestorContactEmail VARCHAR2(4000);
    gestorTabela NUMBER;
    codCondicaoComercial NUMBER;
    leiloeiroEntityId NUMBER;
    isencaoDeTaxa VARCHAR2(1);
    v_exists NUMBER;
BEGIN
    gestorPortal := 2;
    usuarioIntegracao1 := 'nws.integracao';
    usuarioIntegracao2 := 'nws.integracao2';
    
    -- INICIO DADOS CUSTOMIZAVEIS
    gestorEntityId := {gestorEntityId};
    leiloeiroEntityId := {leiloeiroEntityId};
    gestorNome := '{gestorNome}';
    storeNome := '{storeNome}';
    numeroRegistroJunta := '{numeroRegistroJunta}';
    gestorId := {gestorId};
    gestorLogo := '{gestorLogo}';
    storeUri := '{storeUri}';
    gestorContactEmail := '{gestorContactEmail}';
    gestorTabela := {gestorTabela};
    -- FIM DADOS CUSTOMIZAVEIS
    INSERT INTO REL_GESTOR_AUCTIONEER (GESTOR_ID, ENTITY_ID) VALUES(gestorId,leiloeiroEntityId);

    -- ETAPA 1 - CRIAR GESTOR

    -- Atribuir papel de gestor para entity
    --INSERT INTO REL_ROLE_ENTITY (ENTITY_ID,ROLE_ID) VALUES (gestorEntityId,40);
    --INSERT INTO INTER_ENTITY (ENTITY_ID, ENTITY_PARENT_ID, ROLE_ID) VALUES (gestorEntityId,gestorEntityId,40); 

    -- Cadastrar gestor 
    --INSERT INTO GESTOR (GESTOR_ID, GESTOR, ENTITY_ID, GESTOR_TITLE, GESTOR_DESC, GESTOR_INATIVO, EREG_PORTAL_ID)
    --VALUES (gestorId, gestorNome, gestorEntityId, gestorNome, gestorNome, 'F', gestorPortal);
    --desc gestor;
        
    --INSERT INTO GESTOR_SETTINGS (GESTOR_ID,SHOW_ITENS_PORCENTAGEM,COUNTRY_CODE,COD_ERP_SYSTEM,ERP_KEY,AUTO_SALE_START,SYSTEM_CONTACT_EMAIL,AUTO_SALE_GENERATE,GESTOR_CONTACT_EMAIL,COD_PROJETO_LEILAO, PLATFORM_LICENSOR_ID) 
    --  values (gestorId,'2,3','1',2,'CORPORE_RM','01/01/1900','transaction-team@superbid.net','T',gestorContactEmail,130487, 2);



    --INSERT INTO GESTOR_GEO_APPROVAL_DEFAULT (EREF_COUNTRY_CODE, GESTOR_ID) VALUES (1,gestorId);

    -- Projeto Comercial (61922 - Superbid Webservices)
    --INSERT INTO COMMERCIAL_PROJECT (COMMERCIAL_PROJECT_DESC,COMMERCIAL_PROJECT_STATUS_ID,OWNER_ID,YOUR_REFERENCE,CREATED_AT,UPDATED_AT,CLOSE_AT,GESTOR_ID,ECONOMIC_GROUP_ID)
    --     values ('PROJETO PADRAO','1','61922','',SYSDATE,null,SYSDATE,gestorId,null);

    -- Dar acesso as APIS ao usuario do administrativo ( GATE , Plataforma Leiloes, etc.. )
    --SELECT PERFIL_ID INTO usuarioIntegracao1PerfilId FROM PERFIL WHERE ENTITY_ID IN (SELECT ENTITY_ID FROM LOGIN WHERE LOGIN_NAME = usuarioIntegracao1) AND EREG_PORTAL_ID = gestorPortal;

    --INSERT INTO PERFIL_PERMISSAO (PERFIL_ID, MODULO_ID, CREATION_DATE, PAPEL_ID, GESTOR_ID)  VALUES (usuarioIntegracao1PerfilId,'PRG0002',SYSDATE,35,gestorId); -- Operador do Pregão
    --INSERT INTO PERFIL_PERMISSAO (PERFIL_ID, MODULO_ID, CREATION_DATE, PAPEL_ID, GESTOR_ID)  VALUES (usuarioIntegracao1PerfilId,'CDV0002',SYSDATE,36,gestorId); -- Operador Condicao de Venda
    --INSERT INTO PERFIL_PERMISSAO (PERFIL_ID, MODULO_ID, CREATION_DATE, PAPEL_ID, GESTOR_ID)  VALUES (usuarioIntegracao1PerfilId,'LOT0002',SYSDATE,11,gestorId); -- Operador do modulo loteamento Superbid
    --INSERT INTO PERFIL_PERMISSAO (PERFIL_ID, MODULO_ID, CREATION_DATE, PAPEL_ID, GESTOR_ID)  VALUES (usuarioIntegracao1PerfilId,'CCF',SYSDATE,71,gestorId); -- Adminstrador do Modulo
    --INSERT INTO PERFIL_PERMISSAO (PERFIL_ID, MODULO_ID, CREATION_DATE, PAPEL_ID, GESTOR_ID)  VALUES (usuarioIntegracao1PerfilId,'CPC',SYSDATE,106,gestorId); -- Administrador do Módulo
    --INSERT INTO PERFIL_PERMISSAO (PERFIL_ID, MODULO_ID, CREATION_DATE, PAPEL_ID, GESTOR_ID)  VALUES (usuarioIntegracao1PerfilId,'CDA',SYSDATE,111,gestorId); -- Adminstrador CDA - GATE 1.0

    -- Dar acesso as APIS ao usuario do administrativo ( GATE , Plataforma Leiloes, etc.. )
    --SELECT PERFIL_ID INTO usuarioIntegracao2PerfilId FROM PERFIL WHERE ENTITY_ID IN (SELECT ENTITY_ID FROM LOGIN WHERE LOGIN_NAME = usuarioIntegracao2) AND EREG_PORTAL_ID = gestorPortal;

    --INSERT INTO PERFIL_PERMISSAO (PERFIL_ID, MODULO_ID, CREATION_DATE, PAPEL_ID, GESTOR_ID)  VALUES (usuarioIntegracao2PerfilId,'PRG0002',SYSDATE,35,gestorId); -- Operador do Pregão
    --INSERT INTO PERFIL_PERMISSAO (PERFIL_ID, MODULO_ID, CREATION_DATE, PAPEL_ID, GESTOR_ID)  VALUES (usuarioIntegracao2PerfilId,'CDV0002',SYSDATE,36,gestorId); -- Operador Condicao de Venda
    --INSERT INTO PERFIL_PERMISSAO (PERFIL_ID, MODULO_ID, CREATION_DATE, PAPEL_ID, GESTOR_ID)  VALUES (usuarioIntegracao2PerfilId,'LOT0002',SYSDATE,11,gestorId); -- Operador do modulo loteamento Superbid
    --INSERT INTO PERFIL_PERMISSAO (PERFIL_ID, MODULO_ID, CREATION_DATE, PAPEL_ID, GESTOR_ID)  VALUES (usuarioIntegracao2PerfilId,'CCF',SYSDATE,71,gestorId); -- Adminstrador do Modulo
    --INSERT INTO PERFIL_PERMISSAO (PERFIL_ID, MODULO_ID, CREATION_DATE, PAPEL_ID, GESTOR_ID)  VALUES (usuarioIntegracao2PerfilId,'CPC',SYSDATE,106,gestorId); -- Administrador do Módulo
    --INSERT INTO PERFIL_PERMISSAO (PERFIL_ID, MODULO_ID, CREATION_DATE, PAPEL_ID, GESTOR_ID)  VALUES (usuarioIntegracao2PerfilId,'CDA',SYSDATE,111,gestorId); -- Adminstrador CDA - GATE 1.0

    -- SETUP TRANSACIONAL FINANCEIRO

    -- Forma de Pagamento
    --INSERT INTO FL_FORMA_PAGAMENTO_GESTOR VALUES(gestorId,2); --Depósito
    --INSERT INTO FL_FORMA_PAGAMENTO_GESTOR VALUES(gestorId,9); --S4Payments
    --INSERT INTO FL_FORMA_PAGAMENTO_GESTOR VALUES(gestorId,11); --Guia de depósito Judicial

    -- Itens de Pagamento - 1º Split
    --INSERT INTO FL_TIPO_ITEM_PAG_GESTOR(COD_GESTOR, COD_TIPO_ITEM_PAGAMENTO, DATA_CRIACAO, STATUS, ORDEM_BAIXA) VALUES(gestorId, 1, SYSDATE, 'T', 3); --Pagamento do lote
    --INSERT INTO FL_TIPO_ITEM_PAG_GESTOR(COD_GESTOR, COD_TIPO_ITEM_PAGAMENTO, DATA_CRIACAO, STATUS, ORDEM_BAIXA) VALUES(gestorId, 2, SYSDATE, 'T', 1); --Comissão do leiloeiro
    --INSERT INTO FL_TIPO_ITEM_PAG_GESTOR(COD_GESTOR, COD_TIPO_ITEM_PAGAMENTO, DATA_CRIACAO, STATUS, ORDEM_BAIXA) VALUES(gestorId, 5, SYSDATE, 'T', 2); --Encargos de Administração
    --INSERT INTO FL_TIPO_ITEM_PAG_GESTOR(COD_GESTOR, COD_TIPO_ITEM_PAGAMENTO, DATA_CRIACAO, STATUS, ORDEM_BAIXA) VALUES(gestorId, 3, SYSDATE, 'T', 2); --Buyers

    -- Itens de Serviço - 2º Split
    --INSERT INTO FL_TIPO_ITEM_SERV_GESTOR(COD_GESTOR, COD_TIPO_ITEM_SERVICO, STATUS) VALUES(gestorId, 1, 'T'); --Vendedor
    --INSERT INTO FL_TIPO_ITEM_SERV_GESTOR(COD_GESTOR, COD_TIPO_ITEM_SERVICO, STATUS) VALUES(gestorId, 2, 'T'); --Licenciamento
    --INSERT INTO FL_TIPO_ITEM_SERV_GESTOR(COD_GESTOR, COD_TIPO_ITEM_SERVICO, STATUS) VALUES(gestorId, 3, 'T'); --Assessoria

    -- SETUP LOJA
    INSERT INTO SBINS.STORE (ID, NAME,CREATED_AT,UPDATED_AT,PORTAL_ID,VISIBLE_ON_PORTAL,HIGHLIGHT,LOGO_URI,DESCRIPTION,POSITION,EXTERNAL_LINK,VISIBLE_ON_PORTAL_BANNER,LAST_UPDATE_DATE,STORE_URI) 
    values ((SELECT MAX(ID)+1 FROM STORE),UPPER(storeNome),SYSDATE,SYSDATE,15,'T','T',gestorLogo,UPPER(storeNome),null,null,'T',SYSDATE,storeUri) RETURNING ID INTO storeId;

    INSERT INTO REL_STORE_EVENT_MANAGER ( STORE_ID, EVENT_MANAGER_ID ) VALUES ( storeId, gestorId );

    -- SETUP LEILOEIRO
    IF numeroRegistroJunta IS NOT NULL THEN

    INSERT INTO INTER_ENTITY IE (ENTITY_ID, ENTITY_PARENT_ID, ROLE_ID) VALUES (gestorEntityId,gestorEntityId,11);
    INSERT INTO DOCUMENT (DOCUMENT_NUMBER , DOCUMENT_TYPE_ID, ENTITY_ID) VALUES (numeroRegistroJunta, 6, gestorEntityId);
    INSERT INTO REL_GESTOR_AUCTIONEER (GESTOR_ID, ENTITY_ID) VALUES(gestorId,gestorEntityId);

    END IF;

    -- NOVO PERMISSIONAMENTO FINLEI
    --INSERT INTO gestor_acesso (GESTOR_ID,GESTOR_ID_PAI) VALUES(gestorId,114);

    -- CRIAR CONDICAO DE PLATAFORMA
    --insert into fl_ccvenda (COD_CONDICAO_COMERCIAL,DESC_CONDICAO_COMERCIAL,COD_TIPO_TRANSACAO,COD_GESTOR,COD_VENDEDOR,COD_EVENTO,COD_OFERTA,COD_FORMA_PAGAMENTO,COD_FAVORECIDO,DIAS_VENCIMENTO,INSTRUCAO_PAGAMENTO,DATA_CRIACAO,DATA_ATUALIZACAO,COD_STATUS,MIN_PORCENTAGEM_ENTRADA,MAX_QUANTIDADE_PARCELAS,AFTER_CASHOUT,COBRANCA_PLATAFORMA,DATA_EXPIRACAO,DIAS_CONDICIONAL,TIPO_FAVORECIDO)
    --  values ((SELECT MAX(COD_CONDICAO_COMERCIAL)+1 FROM fl_ccvenda),gestorId || ' ' || gestorNome || ' - TABELA ' || gestorTabela,1,gestorId,null,null,null,null,null,null,null,SYSDATE,SYSDATE,2,null,null,null,'T',null,null,null) RETURNING COD_CONDICAO_COMERCIAL INTO codCondicaoComercial;


    --insert into fl_ccvenda_item (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO) values (codCondicaoComercial,2);


    --insert into fl_ccvenda_split (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_TIPO_ITEM_SERVICO,COD_FAVORECIDO,COD_TIPO_COBRANCA,COD_BASE_CALCULO,PORCENTAGEM,VALOR,VALOR_MAXIMO)
    --  values (codCondicaoComercial,2,2,1399790,3,1,null,null,null);

    -- INICIO TABELA 1
    IF gestorTabela = 1 THEN

        insert into fl_ccvenda_split_faixa (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_TIPO_ITEM_SERVICO,VALOR_INICIAL,VALOR_FINAL,PORCENTAGEM,VALOR)
            values (codCondicaoComercial,'2','2','3000,01','10000',null,'50');
        insert into fl_ccvenda_split_faixa (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_TIPO_ITEM_SERVICO,VALOR_INICIAL,VALOR_FINAL,PORCENTAGEM,VALOR)
            values (codCondicaoComercial,'2','2','10000,01','30000',null,'150');
        insert into fl_ccvenda_split_faixa (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_TIPO_ITEM_SERVICO,VALOR_INICIAL,VALOR_FINAL,PORCENTAGEM,VALOR)
            values (codCondicaoComercial,'2','2','30000,01','100000',null,'250');
        insert into fl_ccvenda_split_faixa (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_TIPO_ITEM_SERVICO,VALOR_INICIAL,VALOR_FINAL,PORCENTAGEM,VALOR)
            values (codCondicaoComercial,'2','2','100000,01','999999999999',null,'350');

    END IF;

    -- FIM TABELA 1

    -- INICIO TABELA 2
    IF gestorTabela = 2 THEN

        insert into fl_ccvenda_split_faixa (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_TIPO_ITEM_SERVICO,VALOR_INICIAL,VALOR_FINAL,PORCENTAGEM,VALOR)
            values (codCondicaoComercial,'2','2','3000,01','10000',null,'50');
        insert into fl_ccvenda_split_faixa (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_TIPO_ITEM_SERVICO,VALOR_INICIAL,VALOR_FINAL,PORCENTAGEM,VALOR)
            values (codCondicaoComercial,'2','2','10000,01','30000',null,'150');
        insert into fl_ccvenda_split_faixa (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_TIPO_ITEM_SERVICO,VALOR_INICIAL,VALOR_FINAL,PORCENTAGEM,VALOR)
            values (codCondicaoComercial,'2','2','30000,01','100000',null,'350');
        insert into fl_ccvenda_split_faixa (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_TIPO_ITEM_SERVICO,VALOR_INICIAL,VALOR_FINAL,PORCENTAGEM,VALOR)
            values (codCondicaoComercial,'2','2','100000,01','300000',null,'600');
        insert into fl_ccvenda_split_faixa (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_TIPO_ITEM_SERVICO,VALOR_INICIAL,VALOR_FINAL,PORCENTAGEM,VALOR)
            values (codCondicaoComercial,'2','2','300000,01','999999999999',null,'1000');

    END IF;

    -- FIM TABELA 2

    -- INICIO TABELA 3
    IF gestorTabela = 3 THEN

        insert into fl_ccvenda_split_faixa (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_TIPO_ITEM_SERVICO,VALOR_INICIAL,VALOR_FINAL,PORCENTAGEM,VALOR)
            values (codCondicaoComercial,'2','2','0','10000',null,'50');
        insert into fl_ccvenda_split_faixa (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_TIPO_ITEM_SERVICO,VALOR_INICIAL,VALOR_FINAL,PORCENTAGEM,VALOR)
            values (codCondicaoComercial,'2','2','10000,01','30000',null,'150');
        insert into fl_ccvenda_split_faixa (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_TIPO_ITEM_SERVICO,VALOR_INICIAL,VALOR_FINAL,PORCENTAGEM,VALOR)
            values (codCondicaoComercial,'2','2','30000,01','100000',null,'350');
        insert into fl_ccvenda_split_faixa (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_TIPO_ITEM_SERVICO,VALOR_INICIAL,VALOR_FINAL,PORCENTAGEM,VALOR)
            values (codCondicaoComercial,'2','2','100000,01','300000',null,'600');
        insert into fl_ccvenda_split_faixa (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_TIPO_ITEM_SERVICO,VALOR_INICIAL,VALOR_FINAL,PORCENTAGEM,VALOR)
            values (codCondicaoComercial,'2','2','300000,01','999999999999',null,'1000');

    END IF;

    -- FIM TABELA 3

    -- INICIO TABELA 4
    IF gestorTabela = 4 THEN

        insert into fl_ccvenda_split_faixa (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_TIPO_ITEM_SERVICO,VALOR_INICIAL,VALOR_FINAL,PORCENTAGEM,VALOR)
            values (codCondicaoComercial,'2','2','1','1000',null,'10');
        insert into fl_ccvenda_split_faixa (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_TIPO_ITEM_SERVICO,VALOR_INICIAL,VALOR_FINAL,PORCENTAGEM,VALOR)
            values (codCondicaoComercial,'2','2','1000,01','2000',null,'25');
        insert into fl_ccvenda_split_faixa (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_TIPO_ITEM_SERVICO,VALOR_INICIAL,VALOR_FINAL,PORCENTAGEM,VALOR)
            values (codCondicaoComercial,'2','2','2000,01','5000',null,'50');
        insert into fl_ccvenda_split_faixa (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_TIPO_ITEM_SERVICO,VALOR_INICIAL,VALOR_FINAL,PORCENTAGEM,VALOR)
            values (codCondicaoComercial,'2','2','5000,01','10000',null,'120');
        insert into fl_ccvenda_split_faixa (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_TIPO_ITEM_SERVICO,VALOR_INICIAL,VALOR_FINAL,PORCENTAGEM,VALOR)
            values (codCondicaoComercial,'2','2','10000,01','30000',null,'250');
        insert into fl_ccvenda_split_faixa (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_TIPO_ITEM_SERVICO,VALOR_INICIAL,VALOR_FINAL,PORCENTAGEM,VALOR)
            values (codCondicaoComercial,'2','2','30000,01','70000',null,'500');
        insert into fl_ccvenda_split_faixa (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_TIPO_ITEM_SERVICO,VALOR_INICIAL,VALOR_FINAL,PORCENTAGEM,VALOR)
            values (codCondicaoComercial,'2','2','70000,01','150000',null,'1000');
        insert into fl_ccvenda_split_faixa (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_TIPO_ITEM_SERVICO,VALOR_INICIAL,VALOR_FINAL,PORCENTAGEM,VALOR)
            values (codCondicaoComercial,'2','2','150000,01','300000',null,'2000');
        insert into fl_ccvenda_split_faixa (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_TIPO_ITEM_SERVICO,VALOR_INICIAL,VALOR_FINAL,PORCENTAGEM,VALOR)
            values (codCondicaoComercial,'2','2','300000,01','500000',null,'3000');
        insert into fl_ccvenda_split_faixa (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_TIPO_ITEM_SERVICO,VALOR_INICIAL,VALOR_FINAL,PORCENTAGEM,VALOR)
            values (codCondicaoComercial,'2','2','500000,01','1000000',null,'5000');
        insert into fl_ccvenda_split_faixa (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_TIPO_ITEM_SERVICO,VALOR_INICIAL,VALOR_FINAL,PORCENTAGEM,VALOR)
            values (codCondicaoComercial,'2','2','1000000,01','1500000',null,'8000');
        insert into fl_ccvenda_split_faixa (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_TIPO_ITEM_SERVICO,VALOR_INICIAL,VALOR_FINAL,PORCENTAGEM,VALOR)
            values (codCondicaoComercial,'2','2','1500000,01','3000000',null,'10000');
        insert into fl_ccvenda_split_faixa (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_TIPO_ITEM_SERVICO,VALOR_INICIAL,VALOR_FINAL,PORCENTAGEM,VALOR)
            values (codCondicaoComercial,'2','2','3000000,01','5000000',null,'20000');
        insert into fl_ccvenda_split_faixa (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_TIPO_ITEM_SERVICO,VALOR_INICIAL,VALOR_FINAL,PORCENTAGEM,VALOR)
            values (codCondicaoComercial,'2','2','5000000,01','10000000',null,'30000');
        insert into fl_ccvenda_split_faixa (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_TIPO_ITEM_SERVICO,VALOR_INICIAL,VALOR_FINAL,PORCENTAGEM,VALOR)
            values (codCondicaoComercial,'2','2','10000000,01','50000000',null,'40000');
        insert into fl_ccvenda_split_faixa (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_TIPO_ITEM_SERVICO,VALOR_INICIAL,VALOR_FINAL,PORCENTAGEM,VALOR)
            values (codCondicaoComercial,'2','2','50000000,01','999999999999',null,'75000');

    END IF;

    -- FIM TABELA 4

    --INICIO TABELA 5

    IF gestorTabela = 5 THEN

        insert into fl_ccvenda_split_faixa (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_TIPO_ITEM_SERVICO,VALOR_INICIAL,VALOR_FINAL,PORCENTAGEM,VALOR)
            values (codCondicaoComercial,'2','2','1','1000',null,'10');
        insert into fl_ccvenda_split_faixa (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_TIPO_ITEM_SERVICO,VALOR_INICIAL,VALOR_FINAL,PORCENTAGEM,VALOR)
            values (codCondicaoComercial,'2','2','1000,01','2000',null,'25');
        insert into fl_ccvenda_split_faixa (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_TIPO_ITEM_SERVICO,VALOR_INICIAL,VALOR_FINAL,PORCENTAGEM,VALOR)
            values (codCondicaoComercial,'2','2','2000,01','5000',null,'50');
        insert into fl_ccvenda_split_faixa (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_TIPO_ITEM_SERVICO,VALOR_INICIAL,VALOR_FINAL,PORCENTAGEM,VALOR)
            values (codCondicaoComercial,'2','2','5000,01','10000',null,'120');
        insert into fl_ccvenda_split_faixa (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_TIPO_ITEM_SERVICO,VALOR_INICIAL,VALOR_FINAL,PORCENTAGEM,VALOR)
            values (codCondicaoComercial,'2','2','10000,01','30000',null,'250');
        insert into fl_ccvenda_split_faixa (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_TIPO_ITEM_SERVICO,VALOR_INICIAL,VALOR_FINAL,PORCENTAGEM,VALOR)
            values (codCondicaoComercial,'2','2','30000,01','70000',null,'500');
        insert into fl_ccvenda_split_faixa (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_TIPO_ITEM_SERVICO,VALOR_INICIAL,VALOR_FINAL,PORCENTAGEM,VALOR)
            values (codCondicaoComercial,'2','2','70000,01','150000',null,'1000');
        insert into fl_ccvenda_split_faixa (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_TIPO_ITEM_SERVICO,VALOR_INICIAL,VALOR_FINAL,PORCENTAGEM,VALOR)
            values (codCondicaoComercial,'2','2','150000,01','300000',null,'2000');
        insert into fl_ccvenda_split_faixa (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_TIPO_ITEM_SERVICO,VALOR_INICIAL,VALOR_FINAL,PORCENTAGEM,VALOR)
            values (codCondicaoComercial,'2','2','300000,01','500000',null,'3000');
        insert into fl_ccvenda_split_faixa (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_TIPO_ITEM_SERVICO,VALOR_INICIAL,VALOR_FINAL,PORCENTAGEM,VALOR)
            values (codCondicaoComercial,'2','2','500000,01','1000000',null,'5000');
        insert into fl_ccvenda_split_faixa (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_TIPO_ITEM_SERVICO,VALOR_INICIAL,VALOR_FINAL,PORCENTAGEM,VALOR)
            values (codCondicaoComercial,'2','2','1000000,01','1500000',null,'8000');
        insert into fl_ccvenda_split_faixa (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_TIPO_ITEM_SERVICO,VALOR_INICIAL,VALOR_FINAL,PORCENTAGEM,VALOR)
            values (codCondicaoComercial,'2','2','1500000,01','3000000',null,'10000');
        insert into fl_ccvenda_split_faixa (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_TIPO_ITEM_SERVICO,VALOR_INICIAL,VALOR_FINAL,PORCENTAGEM,VALOR)
            values (codCondicaoComercial,'2','2','3000000,01','5000000',null,'20000');
        insert into fl_ccvenda_split_faixa (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_TIPO_ITEM_SERVICO,VALOR_INICIAL,VALOR_FINAL,PORCENTAGEM,VALOR)
            values (codCondicaoComercial,'2','2','5000000,01','10000000',null,'30000');
        insert into fl_ccvenda_split_faixa (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_TIPO_ITEM_SERVICO,VALOR_INICIAL,VALOR_FINAL,PORCENTAGEM,VALOR)
            values (codCondicaoComercial,'2','2','10000000,01','50000000',null,'40000');

    END IF;

    --FIM TABELA 5

    --Fim da tabela 5

    END;
    /
""",
        "hispanico": """
DECLARE
    gestorPortal NUMBER;
    usuarioIntegracao1 VARCHAR2(4000);
    usuarioIntegracao1PerfilId NUMBER;
    usuarioIntegracao2 VARCHAR2(4000);
    usuarioIntegracao2PerfilId NUMBER;
    gestorId NUMBER;
    gestorEntityId NUMBER;
    gestorNome VARCHAR2(4000);
    numeroRegistroJunta VARCHAR2(4000);
    storeId NUMBER;
    storeNome VARCHAR2(4000);
    gestorLogo VARCHAR2(4000);
    storeUri VARCHAR2(4000);
    gestorContactEmail VARCHAR2(4000);
    gestorTabela NUMBER;
    codCondicaoComercial NUMBER;
    leiloeiroEntityId NUMBER;
    isencaoDeTaxa VARCHAR2(1);
    v_exists NUMBER;
BEGIN
    gestorPortal := 17;
    
    -- INICIO DADOS CUSTOMIZAVEIS
    gestorEntityId := {gestorEntityId};
    gestorNome := '{gestorNome}';
    storeNome := '{storeNome}';
    numeroRegistroJunta := '{numeroRegistroJunta}';
    gestorId := {gestorId};
    gestorLogo := '{gestorLogo}';
    storeUri := '{storeUri}';
    gestorContactEmail := '{gestorContactEmail}';
    -- FIM DADOS CUSTOMIZAVEIS
    -- ETAPA 1 - CRIAR GESTOR

    -- Atribuir papel de gestor para entity
    --INSERT INTO REL_ROLE_ENTITY (ENTITY_ID,ROLE_ID) VALUES (gestorEntityId,40);
    --INSERT INTO INTER_ENTITY (ENTITY_ID, ENTITY_PARENT_ID, ROLE_ID) VALUES (gestorEntityId,gestorEntityId,40); 

    -- Cadastrar gestor
    --INSERT INTO GESTOR ( GESTOR_ID, GESTOR, ENTITY_ID, GESTOR_TITLE, GESTOR_DESC, GESTOR_INATIVO, EREG_PORTAL_ID)
    --  VALUES  (gestorId, gestorNome, gestorEntityId, gestorNome, gestorNome, 'F', gestorPortal) ;

    --INSERT INTO GESTOR_SETTINGS (GESTOR_ID,SHOW_ITENS_PORCENTAGEM,COUNTRY_CODE,COD_ERP_SYSTEM,ERP_KEY,AUTO_SALE_START,SYSTEM_CONTACT_EMAIL,AUTO_SALE_GENERATE,GESTOR_CONTACT_EMAIL)
    --  values (gestorId,'2,3','1',2,'CORPORE_RM','01/01/1900','transaction-team@superbid.net','T',gestorContactEmail);

    --INSERT INTO GESTOR_GEO_APPROVAL_DEFAULT (EREF_COUNTRY_CODE, GESTOR_ID) VALUES (1,gestorId);

    -- Projeto Comercial (61922 - Superbid Webservices)
    INSERT INTO COMMERCIAL_PROJECT (COMMERCIAL_PROJECT_DESC,COMMERCIAL_PROJECT_STATUS_ID,OWNER_ID,YOUR_REFERENCE,CREATED_AT,UPDATED_AT,CLOSE_AT,GESTOR_ID,ECONOMIC_GROUP_ID)
        values ('PROJETO PADRAO','1','61922','',SYSDATE,null,SYSDATE,gestorId,null);

    -- SETUP TRANSACIONAL FINANCEIRO

    -- Forma de Pagamento
    --INSERT INTO FL_FORMA_PAGAMENTO_GESTOR VALUES(gestorId,2); --Depósito
    --INSERT INTO FL_FORMA_PAGAMENTO_GESTOR VALUES(gestorId,9); --S4Payments
    --INSERT INTO FL_FORMA_PAGAMENTO_GESTOR VALUES(gestorId,11); --Guia de depósito Judicial

    -- Itens de Pagamento - 1º Split
    --INSERT INTO FL_TIPO_ITEM_PAG_GESTOR(COD_GESTOR, COD_TIPO_ITEM_PAGAMENTO, DATA_CRIACAO, STATUS, ORDEM_BAIXA) VALUES(gestorId, 1, SYSDATE, 'T', 3); --Pagamento do lote
    --INSERT INTO FL_TIPO_ITEM_PAG_GESTOR(COD_GESTOR, COD_TIPO_ITEM_PAGAMENTO, DATA_CRIACAO, STATUS, ORDEM_BAIXA) VALUES(gestorId, 2, SYSDATE, 'T', 1); --Comissão do leiloeiro
    --INSERT INTO FL_TIPO_ITEM_PAG_GESTOR(COD_GESTOR, COD_TIPO_ITEM_PAGAMENTO, DATA_CRIACAO, STATUS, ORDEM_BAIXA) VALUES(gestorId, 5, SYSDATE, 'T', 2); --Encargos de Administração
    --INSERT INTO FL_TIPO_ITEM_PAG_GESTOR(COD_GESTOR, COD_TIPO_ITEM_PAGAMENTO, DATA_CRIACAO, STATUS, ORDEM_BAIXA) VALUES(gestorId, 3, SYSDATE, 'T', 2); --Buyers

    -- Itens de Serviço - 2º Split
    --INSERT INTO FL_TIPO_ITEM_SERV_GESTOR(COD_GESTOR, COD_TIPO_ITEM_SERVICO, STATUS) VALUES(gestorId, 1, 'T'); --Vendedor
    --INSERT INTO FL_TIPO_ITEM_SERV_GESTOR(COD_GESTOR, COD_TIPO_ITEM_SERVICO, STATUS) VALUES(gestorId, 2, 'T'); --Licenciamento
    --INSERT INTO FL_TIPO_ITEM_SERV_GESTOR(COD_GESTOR, COD_TIPO_ITEM_SERVICO, STATUS) VALUES(gestorId, 3, 'T'); --Assessoria

    -- SETUP LOJA
    INSERT INTO SBINS.STORE (ID, NAME,CREATED_AT,UPDATED_AT,PORTAL_ID,VISIBLE_ON_PORTAL,HIGHLIGHT,LOGO_URI,DESCRIPTION,POSITION,EXTERNAL_LINK,VISIBLE_ON_PORTAL_BANNER,LAST_UPDATE_DATE,STORE_URI)
    values ((SELECT MAX(ID)+1 FROM STORE),UPPER(storeNome),SYSDATE,SYSDATE,17,'T','T',gestorLogo,UPPER(storeNome),null,null,'T',SYSDATE,storeUri) RETURNING ID INTO storeId;

    INSERT INTO REL_STORE_EVENT_MANAGER ( STORE_ID, EVENT_MANAGER_ID ) VALUES ( storeId, gestorId );

    -- SETUP LEILOEIRO

    --  INSERT INTO REL_GESTOR_AUCTIONEER (GESTOR_ID, ENTITY_ID) VALUES(gestorId,gestorEntityId);

    -- NOVO PERMISSIONAMENTO FINLEI
    INSERT INTO gestor_acesso (GESTOR_ID,GESTOR_ID_PAI) VALUES(gestorId,114);

    -- CRIAR CONDICAO DE PLATAFORMA
    insert into fl_ccvenda (COD_CONDICAO_COMERCIAL,DESC_CONDICAO_COMERCIAL,COD_TIPO_TRANSACAO,COD_GESTOR,COD_VENDEDOR,COD_EVENTO,COD_OFERTA,COD_FORMA_PAGAMENTO,COD_FAVORECIDO,DIAS_VENCIMENTO,INSTRUCAO_PAGAMENTO,DATA_CRIACAO,DATA_ATUALIZACAO,COD_STATUS,MIN_PORCENTAGEM_ENTRADA,MAX_QUANTIDADE_PARCELAS,AFTER_CASHOUT,COBRANCA_PLATAFORMA,DATA_EXPIRACAO,DIAS_CONDICIONAL,TIPO_FAVORECIDO)
    values ((SELECT MAX(COD_CONDICAO_COMERCIAL)+1 FROM fl_ccvenda),gestorId || ' ' || gestorNome || ' - TABELA ' || gestorTabela,1,gestorId,null,null,null,null,null,null,null,SYSDATE,SYSDATE,2,null,null,null,'T',null,null,null) RETURNING COD_CONDICAO_COMERCIAL INTO codCondicaoComercial;
    insert into fl_ccvenda_item (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_FORMA_PAGAMENTO,COD_FAVORECIDO,COD_CONTA_PAG_FAVORECIDO,COD_TIPO_COBRANCA,PORCENTAGEM,VALOR,VALOR_MAXIMO)
    values (codCondicaoComercial,2,9,gestorEntityId,null,2,5,null,null);
    insert into fl_ccvenda_split (COD_CONDICAO_COMERCIAL,COD_TIPO_ITEM_PAGAMENTO,COD_TIPO_ITEM_SERVICO,COD_FAVORECIDO,COD_TIPO_COBRANCA,COD_BASE_CALCULO,PORCENTAGEM,VALOR,VALOR_MAXIMO)
    values (codCondicaoComercial,2,2,1399790,3,1,null,null,null);

    END;
    /
"""
    }
    return templates.get(origem_loja.lower())

def safe_int_conversion(value, default=0):
    if pd.isna(value) or str(value).strip() == '':
        return default
    try:
        return int(float(value))
    except (ValueError, TypeError):
        return default
    
def render_sql_script(config: StoreConfig) -> str:
    template = get_sql_template(config.origemLoja)
    if not template:
        raise ValueError(f"Template not found for origem_loja: {config.origemLoja}")

    return template.format(
        gestorEntityId=config.gestorEntityId,
        gestorNome=config.gestorNome,
        storeNome=config.storeNome,
        numeroRegistroJunta=config.numeroRegistroJunta or '',
        gestorId=config.gestorId or "NULL",
        gestorLogo=config.gestorLogo,
        storeUri=config.storeUri,
        gestorContactEmail=config.gestorContactEmail,
        gestorTabela=config.gestorTabela,
        leiloeiroEntityId=config.leiloeiroEntityId or "NULL",
        isencaoDeTaxa=config.isencaoDeTaxa
    )

@app.post("/generate-sql/")
async def generate_sql(config: StoreConfig):
    try:
        sql_script = render_sql_script(config)
        return {"script": sql_script}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.post("/generate-sql-from-excel/")
async def generate_sql_from_excel(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        df = pd.read_excel(io.BytesIO(contents), header=5)

        df = df.reset_index(drop=True)  # Garante que o índice comece do zero

        expected_headers = {
            'C': 'gestorEntityId',
            'D': 'gestorNome',
            'E': 'storeNome',
            'G': 'numeroRegistroJunta',
            'K': 'gestorLogo',
            'N': 'storeUri',
            'O': 'gestorContactEmail',
            'P': 'gestorTabela',
            'R': 'leiloeiroEntityId',
            'AF': 'origemLoja'
        }

        missing_or_wrong = []

        for col_letter, expected_name in expected_headers.items():
            def column_letter_to_index(col_letter):
                index = 0
                for char in col_letter:
                    index = index * 26 + (ord(char.upper()) - ord('A') + 1)
                return index - 1  # zero-based index
            
            col_index = column_letter_to_index(col_letter)


            if col_index >= len(df.columns):
                missing_or_wrong.append(f"Coluna {col_letter} ({expected_name}) está ausente")
                continue
            actual = str(df.columns[col_index]).strip()
            if actual != expected_name:
                missing_or_wrong.append(f"Coluna {col_letter} deve ser '{expected_name}', mas está como '{actual}'")

        if missing_or_wrong:
            return JSONResponse(
                status_code=400,
                content={"error": "Cabeçalhos incorretos na planilha", "detalhes": missing_or_wrong}
            )

        if df.empty:
            return JSONResponse(status_code=400, content={"error": "A planilha está vazia"})

        sql_scripts = []
        validation_errors = []

        for index, row in df.iterrows():
            store_nome = row.get('storeNome')
            if store_nome is None or str(store_nome).strip() == '':
                continue
            store_nome = str(store_nome).strip()

            try:
                config = StoreConfig(
                    gestorEntityId=safe_int_conversion(row.get('gestorEntityId')),
                    gestorNome=str(row.get('gestorNome', '')).strip(),
                    storeNome=store_nome,
                    numeroRegistroJunta=str(row.get('numeroRegistroJunta', '')).strip(),
                    gestorLogo=str(row.get('gestorLogo', '')).strip(),
                    storeUri=str(row.get('storeUri', '')).strip(),
                    gestorContactEmail=str(row.get('gestorContactEmail', '')).strip(),
                    gestorTabela=safe_int_conversion(row.get('gestorTabela')),
                    leiloeiroEntityId=str(row.get('leiloeiroEntityId', '')).strip(),
                    origemLoja=str(row.get('origemLoja', '')).strip()
                )

                try:
                    sql_result = render_sql_script(config)
                    sql_scripts.append(sql_result)
                except Exception as e:
                    validation_errors.append(f"Linha {index + 7}: {str(e)}")

            except Exception as e:
                validation_errors.append(f"Linha {index + 7}: {str(e)}")

        result = {"scripts": sql_scripts}
        if validation_errors:
            result["warnings"] = validation_errors

        return result

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 
