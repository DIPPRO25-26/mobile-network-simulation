package fer.project.central.exception;

public class BtsNotFoundException extends RuntimeException {
    public BtsNotFoundException(String btsId) {
        super("BTS not found with bts_id: " + btsId);
    }
}
