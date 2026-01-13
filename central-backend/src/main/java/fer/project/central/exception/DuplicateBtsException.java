package fer.project.central.exception;

public class DuplicateBtsException extends RuntimeException {
    public DuplicateBtsException(String btsId) {
        super("BTS with bts_id: " + btsId + " already exists");
    }
}
